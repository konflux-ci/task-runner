# Select an image registry authentication crendential

`select-oci-auth` selects an image registry authentication credential from an
authentication file. By default, it reads from
`$HOME/.docker/config.json`. Alternative authentication file can be specified
via environment variable `AUTHFILE`.

The script matches a credential by either a registry or an image repository. For example,

```
select-oci-auth quay.io
select-oci-auth registry.io/foo/bar:0.3@sha256:1234567...
```

As you can see, the input image reference can have tag and digest, script ignores them.
