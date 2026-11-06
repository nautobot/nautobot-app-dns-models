# PTR Record Model

The PTR Record model represents a Pointer record in DNS. PTR records are used for reverse DNS lookups, mapping an IP address (encoded as a name under `in-addr.arpa` or `ip6.arpa`) to a domain name.

- `name` (string): FQDN of the record, without TLD.
- `zone` (DNSZoneModel): The DNS zone this record belongs to.
- `ttl` (integer): Time to live for the record.
- `description` (string): Description of the record.
- `comment` (string): Comment for the record.
- `enabled` (boolean, default `True`): Indicates whether the record is eligible for publication by external integrations. This app does not publish records or enforce this setting.
- `ptrdname` (string): Domain name that the record points to.
- `ip_address` (IPAddress, optional): The IP Address this record resolves. An IP Address may be linked to many PTR records, and a PTR record may be linked to at most one IP Address. Deleting the IP Address leaves the PTR record in place and clears this field.

When `PTR_IP_ADDRESS_MATCH_ENFORCED` is enabled (the default), the record's fully qualified name (`name` + `zone`) must equal the reverse pointer of the linked IP Address. See [Installing the App in Nautobot](../admin/install.md) for details.

PTR records on the IP Address detail page are those linked through `ip_address`.

## Linking Existing PTR Records

PTR records created before the `ip_address` field existed are not linked to an IP Address. The `link_ptr_records_to_ip_addresses` management command parses each unlinked PTR record's fully qualified name to an IP address and links it when exactly one matching IP Address exists in Nautobot.

By default the command is a dry run. It lists the proposed links and the records it cannot link: records whose IP Address exists in multiple Namespaces, records with no matching IP Address, and records whose names are not full reverse pointers. Review the output, then run it again with `--commit` to apply the links.

```shell
nautobot-server link_ptr_records_to_ip_addresses
nautobot-server link_ptr_records_to_ip_addresses --commit
```

Options:

- `--commit`: Apply the proposed links.
- `--relink`: Also evaluate PTR records that are already linked to an IP Address, and correct links that do not match the record's name.
- `--zone NAME`: Only evaluate PTR records in this zone. May be given more than once.
