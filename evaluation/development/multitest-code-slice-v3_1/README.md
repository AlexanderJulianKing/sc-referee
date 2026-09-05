# Multiple-testing 3.1 question/attestation gate

This directory is the independent design oracle for the development-only correction-scope
question and attestation layer. `QUESTION_ORACLE.json` was authored from Revision 1a sections 3,
4, and 10 plus the immutable opened/corpus source bytes. It was not generated from the 3.1
implementation's output. Tests execute the frozen 3.0 analyzer and the 3.1 question layer over the
entire 140-case population and compare the result with this artifact.

Attestation expected rows cite the asymmetric rules in design sections 7 and 8. In particular,
the complete-scope answer is only a pointer to the answer-independent existing structural proof;
the claimed factor is never proof input.
