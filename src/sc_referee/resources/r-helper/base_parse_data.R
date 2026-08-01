args <- commandArgs(trailingOnly = TRUE)

hex_utf8 <- function(value) {
  value <- enc2utf8(as.character(value))
  if (length(value) == 0L || is.na(value[[1L]])) {
    return("")
  }
  paste(sprintf("%02x", as.integer(charToRaw(value[[1L]]))), collapse = "")
}

emit <- function(fields) {
  writeLines(paste(fields, collapse = "\t"), con = stdout(), sep = "\n", useBytes = TRUE)
}

if (length(args) != 1L) {
  emit(c("HELPER_ERROR", hex_utf8("expected exactly one immutable source path")))
  quit(save = "no", status = 2L)
}

source_path <- args[[1L]]
parsed <- tryCatch(
  parse(file = source_path, keep.source = TRUE, encoding = "UTF-8"),
  error = function(error) error
)

if (inherits(parsed, "error")) {
  emit(c(
    "PARSE_ERROR",
    hex_utf8(class(parsed)[[1L]]),
    hex_utf8(conditionMessage(parsed)),
    hex_utf8(R.version.string)
  ))
  quit(save = "no", status = 0L)
}

rows <- getParseData(parsed, includeText = TRUE)
if (is.null(rows)) {
  rows <- data.frame(
    line1 = integer(), col1 = integer(), line2 = integer(), col2 = integer(),
    id = integer(), parent = integer(), token = character(), terminal = logical(),
    text = character(), stringsAsFactors = FALSE
  )
}

if (nrow(rows) > 100000L) {
  emit(c("OVER_BUDGET", as.character(nrow(rows)), hex_utf8(R.version.string)))
  quit(save = "no", status = 0L)
}

emit(c("OK", hex_utf8(R.version.string), as.character(nrow(rows))))
if (nrow(rows) > 0L) {
  rows <- rows[order(rows$line1, rows$col1, rows$line2, rows$col2, rows$id), , drop = FALSE]
  for (index in seq_len(nrow(rows))) {
    row <- rows[index, , drop = FALSE]
    emit(c(
      "ROW",
      as.character(row$id),
      as.character(row$parent),
      as.character(row$line1),
      as.character(row$col1),
      as.character(row$line2),
      as.character(row$col2),
      if (isTRUE(row$terminal)) "1" else "0",
      hex_utf8(row$token),
      hex_utf8(row$text)
    ))
  }
}
