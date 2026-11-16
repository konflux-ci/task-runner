# Changelog

## 1.0.1

### Fixed

- Calling `select-oci-auth` on a specially crafted `image_ref` argument could inject
  arbitrary `yq` code into the expression that selects a token from the auth file.
  This could cause the script to return different output than the intended token.
  This was not arbitrary code execution in the traditional sense, since a yq expression
  (invoked without `--security-enable-system-operator`) cannot write anywhere except stdout.
  Fixed by passing variables into yq expressions securely.

## 1.0.0

- The initial version of the `select-oci-auth` tool
