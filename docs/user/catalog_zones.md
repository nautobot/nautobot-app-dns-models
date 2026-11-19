# Catalog Zones

+++ 2.4.0

A [DNS zone](../models/dnszone.md) with a `type` of `Catalog` is an [RFC 9432](https://datatracker.ietf.org/doc/html/rfc9432) catalog zone: it lists other zones, called "member zones", for secondary name servers to serve, instead of holding ordinary records.

This app builds the contents of a catalog zone. It does not serve or consume one and it does not configure name servers, so what follows describes data in Nautobot; getting that data to a name server is the job of whatever integration reads it.

## Records

Every record in a catalog zone is system-managed: none can be created, edited, or deleted by hand. Each takes the catalog zone's TTL, a value [RFC 9432 §4.1](https://datatracker.ietf.org/doc/html/rfc9432#section-4.1) gives no meaning; the RFC's own example uses 0. A catalog zone holds:

- one NS record at the zone apex, with `invalid` as its `server`, as [RFC 9432 §4](https://datatracker.ietf.org/doc/html/rfc9432#section-4) recommends
- a `version` TXT record holding `2`, the only schema version RFC 9432 defines
- one PTR record per member, at `<member_label>.zones`, naming the member zone

Saving a catalog zone writes the NS and TXT records. If code that bypasses validation, or a direct database change, has altered or removed them, the next save of the catalog zone restores them. Each PTR record is written when a zone is added to the catalog and deleted when it is removed.

!!! note
    The apex NS record is named `@`, which denotes the zone origin per [RFC 1035 §5.1](https://datatracker.ietf.org/doc/html/rfc1035#section-5.1), and its `server` omits the trailing dot the RFC writes, since that dot is zone file syntax rather than part of the name.

## Rules

A zone is added to a catalog by setting its `catalog_zone`, and removed from it by clearing that field. Adding a zone to a catalog, or removing it, needs change permission on the zone and view permission on the catalog zone.

These rules apply to a member zone:

- A zone moving to another DNS view must be removed from its catalog, or added to one in the new view, in the same edit.
- When a member zone is deleted, its PTR record is removed from the catalog.

These rules apply to a catalog zone:

- A catalog zone cannot be a member of another catalog zone.
- `auto_create_ptr` cannot be enabled on a catalog zone, since no A or AAAA record can exist in one.
- A catalog zone is not a registered name, so it cannot be the zone on a [DNS Registration](../models/dnsregistration.md).
- A catalog zone that has members cannot be moved to another DNS view.
- A catalog zone that still has members cannot be deleted. Remove its members first.

In the web UI:

- Adding a member from the catalog zone offers only zones that are in no catalog.
- Bulk edit refuses the whole selection if any zone cannot take the change.

!!! note
    A change of catalog is recorded in the member zone's change log. The PTR records it writes and deletes are recorded under their own entries, in the same request. The catalog zone's own change log records neither.

## Member Labels

Each member is identified within its catalog by a label, defined in [RFC 9432 §4.1](https://datatracker.ietf.org/doc/html/rfc9432#section-4.1). A label can be given when a zone is added to a catalog; otherwise Nautobot generates one.

Under RFC 9432, a consumer of the catalog treats a label it has not seen before as the arrival of a member, and one that stops appearing as its departure. Nautobot therefore keeps a member's label while the zone remains in the catalog. Renaming a zone or moving it to another catalog gives it a new label, unless a different label is given in the same change.

Changing a member's label tells consumers to reset that member, as [RFC 9432 §5.6](https://datatracker.ietf.org/doc/html/rfc9432#section-5.6) describes.

## Finding and Querying Members

The REST API filters zones by `catalog_zone` (name or ID), `is_catalog_member`, and `has_members`. GraphQL reports `members` on a catalog zone.

## Limitations

The app writes only the schema version and the member list. It does not support the following properties defined by RFC 9432:

- change of ownership ([`coo`, §4.3.1](https://datatracker.ietf.org/doc/html/rfc9432#section-4.3.1))
- groups ([`group`, §4.3.2](https://datatracker.ietf.org/doc/html/rfc9432#section-4.3.2))
- custom properties ([`*.ext`, §4.4](https://datatracker.ietf.org/doc/html/rfc9432#section-4.4))

Without `coo`, consumers treat moving a zone to another catalog as the zone's removal and a new addition.
