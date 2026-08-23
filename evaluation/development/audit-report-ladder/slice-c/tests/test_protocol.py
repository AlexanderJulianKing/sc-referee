from __future__ import annotations

import copy
import hashlib
import itertools
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import StaticWorld1Case
from sc_referee_evaluation.audit_ladder.slice_c.core import (
    ALL_FACETS,
    CONTROLLER_FACETS,
    WORKER_FACETS,
    RefusalFacetV1,
    canonical_frame,
    canonical_json_bytes,
    sha256,
)
from sc_referee_evaluation.audit_ladder.slice_c.protocol import (
    AdmittedWorkerRequestV1,
    admit_worker_request_v1,
    build_worker_request_v1,
    refusal_frame_v1,
    registry_invalid_frame_v1,
    select_refusal_v1,
    validate_worker_response_v1,
)
from sc_referee_evaluation.audit_ladder.slice_c.runtime import read_runtime_artifacts_v1


@pytest.fixture(scope="module")
def world1_worker_request(
    static_world1_case: StaticWorld1Case,
) -> tuple[dict[str, object], bytes]:
    case = static_world1_case
    return build_worker_request_v1(
        registry=case.registry,
        materials=case.materials,
        request=case.request,
        runtime_artifacts=read_runtime_artifacts_v1(),
    )


def test_world1_request_and_success_frame_identities(
    static_world1_case: StaticWorld1Case,
    world1_worker_request: tuple[dict[str, object], bytes],
) -> None:
    value, request_raw = world1_worker_request
    assert (len(request_raw), sha256(request_raw)) == (
        5_039_689,
        "sha256:9bce5ddb0f09e5b2563aa842fc729376c8c08cffc460d7fb75dbce2c143f39fd",
    )
    admitted = admit_worker_request_v1(
        static_world1_case.registry.protocol_bytes,
        request_raw,
    )
    assert type(admitted) is AdmittedWorkerRequestV1
    response_raw = canonical_frame(
        {
            "facts": static_world1_case.h5ad_facts.to_dict(),
            "schema": "slice-c-worker-success-v1",
            "worker_request_sha256": sha256(request_raw),
        }
    )
    assert (len(response_raw), sha256(response_raw)) == (
        44_485,
        "sha256:0421bd58f13ffa12b0f7b08e030cbfb49a1f28f2ca71fc2305d0255795afd686",
    )
    result = validate_worker_response_v1(
        request_value=value,
        request_raw=request_raw,
        response_raw=response_raw,
        require_world1_success=True,
    )
    assert result.facts == static_world1_case.h5ad_facts
    assert result.refusal is None


def test_mixed_old_new_premise_seal_registry_and_request_replay_refuse(
    static_world1_case: StaticWorld1Case,
    world1_worker_request: tuple[dict[str, object], bytes],
) -> None:
    old_premise = Path(
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/"
        "h5ad-tier1-scanpy1115-premise.json"
    ).read_bytes()
    old_seal = Path(
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-design-memos/"
        "audit-report-ladder-slice-c-runtime-root-seal-v1.json"
    ).read_bytes()
    old_registry = Path(
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-design-memos/"
        "audit-report-ladder-slice-c-worker-protocol-v1.json"
    ).read_bytes()
    assert (len(old_registry), sha256(old_registry)) == (
        16_111,
        "sha256:78820fae41f22e69d42b9059a6ea404fa2b748dd34e1be98250eb60184ae6e7e",
    )

    def wrapper(raw: bytes) -> dict[str, object]:
        return {"byte_size": len(raw), "sha256": sha256(raw), "utf8": raw.decode("utf-8")}

    current_value, current_request = world1_worker_request
    for name, raw in (("premise", old_premise), ("root_seal", old_seal)):
        mixed = copy.deepcopy(current_value)
        mixed["artifacts"][name] = wrapper(raw)  # type: ignore[index]
        assert (
            admit_worker_request_v1(
                static_world1_case.registry.protocol_bytes,
                canonical_frame(mixed),
            )
            is RefusalFacetV1.REQUEST_PROTOCOL
        )

    replay = copy.deepcopy(current_value)
    replay["artifacts"]["premise"] = wrapper(old_premise)  # type: ignore[index]
    replay["artifacts"]["root_seal"] = wrapper(old_seal)  # type: ignore[index]
    old_request = canonical_frame(replay)
    assert (len(old_request), sha256(old_request)) == (
        5_039_976,
        "sha256:ad389cbc4531bf645b4400cfec631943e4f1c84bd8e22eaa884b72ae0494cb69",
    )
    assert (
        admit_worker_request_v1(static_world1_case.registry.protocol_bytes, old_request)
        is RefusalFacetV1.REQUEST_PROTOCOL
    )
    assert admit_worker_request_v1(old_registry, current_request) is RefusalFacetV1.REGISTRY_INVALID

    stale_registry = copy.deepcopy(static_world1_case.registry.protocol)
    stale_registry["artifacts"]["premise"] = {  # type: ignore[index]
        "byte_size": len(old_premise),
        "sha256": sha256(old_premise),
    }
    assert (
        admit_worker_request_v1(canonical_frame(stale_registry), current_request)
        is RefusalFacetV1.REGISTRY_INVALID
    )

    old_response = canonical_frame(
        {
            "facts": static_world1_case.h5ad_facts.to_dict(),
            "schema": "slice-c-worker-success-v1",
            "worker_request_sha256": sha256(old_request),
        }
    )
    assert (len(old_response), sha256(old_response)) == (
        44_485,
        "sha256:54c226d899416e5d7bc92e9ceeea09ea4d887efaadcb5f5696c7cf8867ef0d8e",
    )
    result = validate_worker_response_v1(
        request_value=current_value,
        request_raw=current_request,
        response_raw=old_response,
        require_world1_success=True,
    )
    assert result.facts is None
    assert result.refusal is RefusalFacetV1.RESPONSE_PROTOCOL


def test_closed_refusal_ownership_all_names_and_controller_worker_pairs() -> None:
    for facet in CONTROLLER_FACETS:
        result = validate_worker_response_v1(
            request_value={},
            request_raw=b"request\n",
            response_raw=refusal_frame_v1(facet),
            require_world1_success=False,
        )
        assert result.facts is None
        assert result.refusal is RefusalFacetV1.RESPONSE_PROTOCOL
    for facet in WORKER_FACETS:
        result = validate_worker_response_v1(
            request_value={},
            request_raw=b"request\n",
            response_raw=refusal_frame_v1(facet),
            require_world1_success=False,
        )
        assert result.facts is None
        assert result.refusal is facet
    pairs = 0
    for controller in CONTROLLER_FACETS:
        for worker in WORKER_FACETS:
            assert select_refusal_v1({controller}, worker_named=worker) is controller
            pairs += 1
    assert pairs == 119


def test_total_precedence_singles_pairs_and_exhaustive_equivalent_digest() -> None:
    for facet in ALL_FACETS:
        assert select_refusal_v1({facet}) is facet
    pair_count = 0
    for first, second in itertools.combinations(ALL_FACETS, 2):
        assert select_refusal_v1({second, first}) is first
        pair_count += 1
    assert pair_count == 276

    # The cleared derivation hashes one zero-based selected-rank byte for each
    # increasing nonempty 24-bit mask.  The lowest set bit is the proven first rank.
    digest = hashlib.sha256()
    partition = [0] * 24
    block = bytearray()
    for mask in range(1, 1 << 24):
        rank = (mask & -mask).bit_length() - 1
        partition[rank] += 1
        block.append(rank)
        if len(block) == 1_048_576:
            digest.update(block)
            block.clear()
    digest.update(block)
    assert partition == [1 << rank for rank in range(23, -1, -1)]
    assert digest.hexdigest() == (
        "6d1703bb3eaf3d719c723828a6f15f34f1ecc15955a2614c5e43aaa8a3e58865"
    )


def _registry_mutations(raw: bytes, value: dict[str, object]) -> Iterator[bytes]:
    controller = [item.value for item in CONTROLLER_FACETS]
    worker = [item.value for item in WORKER_FACETS]
    refusal = copy.deepcopy(value["responses"])["refusal"]  # type: ignore[index]

    def changed(path: str, replacement: object) -> bytes:
        candidate = copy.deepcopy(value)
        candidate_refusal = candidate["responses"]["refusal"]  # type: ignore[index]
        if path == "controller":
            candidate_refusal["controller_only_facets"] = replacement
        else:
            candidate_refusal["worker_emittable_facets"] = replacement
        return canonical_frame(candidate)

    for index in range(len(controller)):
        yield changed("controller", controller[:index] + controller[index + 1 :])
    for index in range(len(controller)):
        for alternate in worker:
            replacement = controller.copy()
            replacement[index] = alternate
            yield changed("controller", replacement)
    for index in range(len(controller) + 1):
        for alternate in worker:
            replacement = controller.copy()
            replacement.insert(index, alternate)
            yield changed("controller", replacement)
    for left, right in itertools.combinations(range(len(controller)), 2):
        replacement = controller.copy()
        replacement[left], replacement[right] = replacement[right], replacement[left]
        yield changed("controller", replacement)
    missing = copy.deepcopy(value)
    del missing["responses"]["refusal"]["controller_only_facets"]  # type: ignore[index]
    yield canonical_frame(missing)
    for wrong in (None, 1, "controller", {}):
        yield changed("controller", wrong)

    for index in range(len(worker)):
        yield changed("worker", worker[:index] + worker[index + 1 :])
    for index in range(len(worker)):
        for alternate in controller:
            replacement = worker.copy()
            replacement[index] = alternate
            yield changed("worker", replacement)
    for index in range(len(worker) + 1):
        for alternate in controller:
            replacement = worker.copy()
            replacement.insert(index, alternate)
            yield changed("worker", replacement)
    for left, right in itertools.combinations(range(len(worker)), 2):
        replacement = worker.copy()
        replacement[left], replacement[right] = replacement[right], replacement[left]
        yield changed("worker", replacement)
    missing = copy.deepcopy(value)
    del missing["responses"]["refusal"]["worker_emittable_facets"]  # type: ignore[index]
    yield canonical_frame(missing)
    for wrong in (None, 1, "worker", {}):
        yield changed("worker", wrong)

    raw_siblings = (
        raw[:-1],
        raw + b"\n",
        raw[:-1] + b"\r\n",
        b" " + raw,
        b"\xef\xbb\xbf" + raw,
        b"\xff" + raw,
        raw.replace(b"{", b"{ ", 1),
        raw.replace(b'"artifacts"', b'"z-artifacts"', 1),
        raw[:-1] + b',"schema":"duplicate"}\n',
        b"\x00" + raw,
        b"\n" + raw,
    )
    yield from raw_siblings

    correlated = copy.deepcopy(value)
    for key in ("controller_precedence",):
        correlated[key][0], correlated[key][1] = correlated[key][1], correlated[key][0]  # type: ignore[index]
    for key in ("precedence", "refusal_facets"):
        correlated[key][0], correlated[key][1] = correlated[key][1], correlated[key][0]  # type: ignore[index]
    correlated_refusal = correlated["responses"]["refusal"]  # type: ignore[index]
    (
        correlated_refusal["controller_only_facets"][0],
        correlated_refusal["controller_only_facets"][1],
    ) = (
        correlated_refusal["controller_only_facets"][1],
        correlated_refusal["controller_only_facets"][0],
    )
    yield canonical_frame(correlated)
    assert refusal["controller_only_facets"] == controller
    assert refusal["worker_emittable_facets"] == worker


def test_all_registry_mutations_precede_three_request_carriers(
    static_world1_case: StaticWorld1Case,
    world1_worker_request: tuple[dict[str, object], bytes],
) -> None:
    raw = static_world1_case.registry.protocol_bytes
    semantic_mutations = tuple(_registry_mutations(raw, static_world1_case.registry.protocol))
    assert len(semantic_mutations) == 703
    positional_mutations: list[bytes] = []
    for index in range(4_951):
        candidate = bytearray(raw)
        candidate[index] ^= 1
        positional_mutations.append(bytes(candidate))
    attempted = (*semantic_mutations, *positional_mutations, *semantic_mutations[:96])
    mutations = set(attempted)
    assert len(attempted) == 5_750
    assert len(mutations) == 5_654
    oversized = b"x" * 22_371_001
    carriers = (world1_worker_request[1], b"{malformed\n", oversized)
    invocations = 0
    for mutation in mutations:
        for carrier in carriers:
            assert admit_worker_request_v1(mutation, carrier) is RefusalFacetV1.REGISTRY_INVALID
            invocations += 1
    assert invocations == 16_962
    fixed = registry_invalid_frame_v1()
    assert (len(fixed), sha256(fixed)) == (
        66,
        "sha256:1f3e22be0961918e9214d6cd4abe2584e3028f2f7be3eddc2432ea1e2f81bdac",
    )


def _request_relation_mutations(value: dict[str, object]) -> list[bytes]:
    candidates: list[dict[str, object]] = []

    def candidate() -> dict[str, object]:
        item = copy.deepcopy(value)
        candidates.append(item)
        return item

    item = candidate()
    del item["repository"]  # type: ignore[arg-type]
    item = candidate()
    item["unknown"] = 1
    item = candidate()
    item["h5ad_payload"]["payload_b64"] += "="  # type: ignore[index,operator]
    item = candidate()
    item["h5ad_payload"]["byte_size"] = 330_007  # type: ignore[index]
    item = candidate()
    item["h5ad_payload"]["sha256"] = "sha256:" + "0" * 64  # type: ignore[index]
    item = candidate()
    item["source_payload"]["byte_size"] = 1_014  # type: ignore[index]
    item = candidate()
    item["source_payload"]["sha256"] = "sha256:" + "0" * 64  # type: ignore[index]
    item = candidate()
    item["slice_c_request"]["source_path"] = "stale.py"  # type: ignore[index]
    item = candidate()
    item["slice_c_request"]["obs_column"] = True  # type: ignore[index]
    item = candidate()
    item["repository"]["file_records"].pop()  # type: ignore[index,union-attr]
    item = candidate()
    item["repository"]["file_records"].reverse()  # type: ignore[index,union-attr]
    item = candidate()
    item["repository"]["file_records"].append(  # type: ignore[index,union-attr]
        copy.deepcopy(item["repository"]["file_records"][0])  # type: ignore[index]
    )
    item = candidate()
    item["repository"]["snapshot_ref"] = "snapshot:" + "0" * 20  # type: ignore[index]
    item = candidate()
    item["repository"]["file_manifest"]["entry_count"] = 1  # type: ignore[index]
    item = candidate()
    item["repository"]["file_manifest"]["sha256"] = "sha256:" + "0" * 64  # type: ignore[index]
    item = candidate()
    item["repository"]["selected_materials"]["h5ad"]["material_ref"] = (  # type: ignore[index]
        "material:" + "0" * 20
    )
    item = candidate()
    item["repository"]["selected_materials"]["source"]["asset_identity"][  # type: ignore[index]
        "byte_size"
    ] = 0
    item = candidate()
    item["repository"]["selected_materials"]["source"]["frozen_material"][  # type: ignore[index]
        "utf8"
    ] += " "
    item = candidate()
    item["repository"]["snapshot_identity"]["utf8"] += " "  # type: ignore[index,operator]
    return [canonical_frame(item) for item in candidates]


def test_request_payload_inventory_private_and_preimage_forgery_routes(
    static_world1_case: StaticWorld1Case,
    world1_worker_request: tuple[dict[str, object], bytes],
) -> None:
    mutations = _request_relation_mutations(world1_worker_request[0])
    assert len(mutations) == 19
    assert len(set(mutations)) == 19
    for mutation in mutations:
        assert (
            admit_worker_request_v1(static_world1_case.registry.protocol_bytes, mutation)
            is RefusalFacetV1.REQUEST_PROTOCOL
        )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda raw: raw[:-1],
        lambda raw: raw + b"\n",
        lambda raw: b"\xff" + raw,
        lambda raw: raw.replace(b'"schema":', b'"schema":0,"schema":', 1),
    ],
)
def test_request_frame_siblings(
    static_world1_case: StaticWorld1Case,
    world1_worker_request: tuple[dict[str, object], bytes],
    mutate: object,
) -> None:
    raw = mutate(world1_worker_request[1])  # type: ignore[operator]
    assert (
        admit_worker_request_v1(static_world1_case.registry.protocol_bytes, raw)
        is RefusalFacetV1.REQUEST_FRAME
    )


def _payload_request(
    base: dict[str, object],
    payload: bytes,
    *,
    obs_column: str,
) -> bytes:
    value = dict(base)
    import base64

    source = b""
    value["source_payload"] = {
        "byte_size": 0,
        "sha256": sha256(source),
        "utf8": "",
    }
    value["h5ad_payload"] = {
        "byte_size": len(payload),
        "payload_b64": base64.b64encode(payload).decode("ascii"),
        "sha256": sha256(payload),
    }
    value["slice_c_request"] = {
        "h5ad_path": "b",
        "obs_column": obs_column,
        "schema": "slice-c-request-v1",
        "source_path": "a",
    }
    value["repository"] = _closed_repository(source, payload)
    return canonical_frame(value)


def _exact_wrapper(value: dict[str, object]) -> dict[str, object]:
    raw = canonical_json_bytes(value)
    return {"byte_size": len(raw), "sha256": sha256(raw), "utf8": raw.decode("utf-8")}


def _closed_repository(source: bytes, h5ad: bytes) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    for path, payload, role in (("a", source, "source"), ("b", h5ad, "h5ad")):
        identity = {
            "byte_size": len(payload),
            "path": path,
            "schema": "slice-c-material-identity-v1",
            "sha256": sha256(payload),
        }
        suffix = sha256(canonical_json_bytes(identity))[7:27]
        entries.append(
            {
                "asset_ref": "asset-identity:" + suffix,
                "file_ref": "file:" + suffix,
                "identity": identity,
                "path": path,
                "payload": payload,
                "role": role,
            }
        )
    snapshot = {
        "files": [entry["identity"] for entry in entries],
        "schema": "slice-c-snapshot-identity-v1",
    }
    snapshot_ref = "snapshot:" + sha256(canonical_json_bytes(snapshot))[7:27]
    file_records: list[dict[str, object]] = []
    selected: dict[str, object] = {}
    for entry in entries:
        path = entry["path"]
        payload = entry["payload"]
        role = entry["role"]
        file_ref = entry["file_ref"]
        asset_ref = entry["asset_ref"]
        assert type(path) is str and type(payload) is bytes and type(role) is str
        assert type(file_ref) is str and type(asset_ref) is str
        file_record = {
            "asset_identity_ref": {
                "record_id": asset_ref,
                "record_type": "asset_identity",
            },
            "byte_size": len(payload),
            "entry_kind": "regular_file",
            "file_record_id": file_ref,
            "path": path,
            "record_type": "file_record",
            "snapshot_ref": {
                "record_id": snapshot_ref,
                "record_type": "repository_snapshot",
            },
        }
        asset = {
            "asset_identity_id": asset_ref,
            "asset_ref": {"record_id": file_ref, "record_type": "file_record"},
            "identity_evidence": {"digest": sha256(payload), "kind": "full_digest"},
            "record_type": "asset_identity",
            "tier": "full_digest",
        }
        frozen = {
            "asset_identity_ref": {
                "record_id": asset_ref,
                "record_type": "asset_identity",
            },
            "byte_size": len(payload),
            "content_member": role + "_payload",
            "file_ref": {"record_id": file_ref, "record_type": "file_record"},
            "path": path,
            "schema": "slice-c-frozen-material-v1",
            "sha256": sha256(payload),
        }
        file_records.append(file_record)
        selected[role] = {
            "asset_identity": _exact_wrapper(asset),
            "frozen_material": _exact_wrapper(frozen),
            "material_ref": "material:" + sha256(canonical_json_bytes(frozen))[7:27],
        }
    manifest_raw = b"".join(canonical_frame(record) for record in file_records)
    return {
        "file_manifest": {
            "byte_size": len(manifest_raw),
            "entry_count": len(file_records),
            "file_manifest_ref": "observed/files.jsonl",
            "sha256": sha256(manifest_raw),
            "utf8": manifest_raw.decode("utf-8"),
        },
        "file_records": [_exact_wrapper(record) for record in file_records],
        "selected_materials": selected,
        "snapshot_identity": _exact_wrapper(snapshot),
        "snapshot_ref": snapshot_ref,
    }


def test_request_limit_and_limit_plus_one_exact_vectors(
    static_world1_case: StaticWorld1Case,
    world1_worker_request: tuple[dict[str, object], bytes],
) -> None:
    payload = b"\x00" * 13_329_363
    at_limit = _payload_request(world1_worker_request[0], payload, obs_column="c" * 19)
    assert (len(at_limit), sha256(at_limit)) == (
        22_371_000,
        "sha256:3448c7c5c2dda09223cd83fc3613834bd442e6f889b8a648365fe7c1fdc22115",
    )
    assert (
        type(admit_worker_request_v1(static_world1_case.registry.protocol_bytes, at_limit))
        is AdmittedWorkerRequestV1
    )
    over_limit = _payload_request(world1_worker_request[0], payload, obs_column="c" * 20)
    assert (len(over_limit), sha256(over_limit)) == (
        22_371_001,
        "sha256:ab61bfe815569a17c0ceb896f6887e293a9079925db9824ee20eb4fa4f9aad5c",
    )
    assert (
        admit_worker_request_v1(static_world1_case.registry.protocol_bytes, over_limit)
        is RefusalFacetV1.REQUEST_BYTES
    )


@pytest.mark.parametrize(
    ("size", "expected_digest"),
    [
        (16_777_216, "475c819668daf89ddcbec69c3b053888c25408c090654e994c233ce377715bbb"),
        (16_777_217, "17ad49ec78b3fd689520a52adf65bc6478737ba88dfdbd99da7b1455d2b272fd"),
    ],
)
def test_decoded_limit_vectors_are_request_bytes_end_to_end(
    static_world1_case: StaticWorld1Case,
    world1_worker_request: tuple[dict[str, object], bytes],
    size: int,
    expected_digest: str,
) -> None:
    raw = _payload_request(world1_worker_request[0], b"\x00" * size, obs_column="c")
    assert len(raw) == 26_968_122
    assert hashlib.sha256(raw).hexdigest() == expected_digest
    assert (
        admit_worker_request_v1(static_world1_case.registry.protocol_bytes, raw)
        is RefusalFacetV1.REQUEST_BYTES
    )


def test_stdout_limit_and_limit_plus_one_exact_vectors(
    static_world1_case: StaticWorld1Case,
    world1_worker_request: tuple[dict[str, object], bytes],
) -> None:
    seed = _payload_request(world1_worker_request[0], b"", obs_column="c")
    assert (len(seed), sha256(seed)) == (
        4_598_463,
        "sha256:655e275a6cd25aea456f85080be463739a13de0c9dbcf892a6a1140536bfc774",
    )
    heavy = "\\" * 1_024
    tuning = "a" * 813
    values = [heavy] * 4_088 + [tuning]
    facts = {
        "matrix-shape": {"column_count": 10, "row_count": 4_089},
        "obs-column-cardinality": {"column": "c", "distinct_count": 2, "n_obs": 4_089},
        "obs-column-quoted-values": {"column": "c", "n_obs": 4_089, "values": values},
        "obs-group-sizes": {
            "column": "c",
            "groups": [
                {"count": 4_088, "value": heavy},
                {"count": 1, "value": tuning},
            ],
            "n_obs": 4_089,
        },
    }
    value = {
        "facts": facts,
        "schema": "slice-c-worker-success-v1",
        "worker_request_sha256": sha256(seed),
    }
    at_limit = canonical_frame(value)
    assert (len(at_limit), sha256(at_limit)) == (
        8_388_608,
        "sha256:9b99bc994c42769d13cf79c3556cc89341a38994c505cdb62203133157e7a506",
    )
    result = validate_worker_response_v1(
        request_value=world1_worker_request[0],
        request_raw=seed,
        response_raw=at_limit,
        require_world1_success=False,
    )
    assert result.refusal is RefusalFacetV1.RESPONSE_PROTOCOL
    facts["matrix-shape"] = {"column_count": 100, "row_count": 4_089}
    over_limit = canonical_frame(value)
    assert (len(over_limit), sha256(over_limit)) == (
        8_388_609,
        "sha256:164678f068dc160c32b4fc7a338be6a3a9adaeec7bc84281140c4628bd08828c",
    )
    result = validate_worker_response_v1(
        request_value=world1_worker_request[0],
        request_raw=seed,
        response_raw=over_limit,
        require_world1_success=False,
    )
    assert result.refusal is RefusalFacetV1.STDOUT
