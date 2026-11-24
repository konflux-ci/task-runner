# Changelog

## 1.0.1

- Fix empty `RETRY_STOP_ON_EXIT_CODES` array expansion under Bash `nounset` mode
  (only affects Bash < 4.4, e.g. the default Bash on macOS)

## 1.0.0

- The initial version of the `retry` tool
