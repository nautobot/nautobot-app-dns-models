# Upgrading the App

Here you will find any steps necessary to upgrade the App in your Nautobot environment.

## Upgrade Guide

When a new release comes out it may be necessary to run a migration of the database to account for any changes in the data models used by this app. Execute the command `nautobot-server post_upgrade` within the runtime environment of your Nautobot installation after updating the `nautobot-dns-models` package via `pip`.

## Case-Insensitive DNS Zone Names

DNS zone names must be unique within a DNS view regardless of letter case (see [Zone Name Uniqueness](../models/dnszone.md#zone-name-uniqueness)). If two zones in the same view have names that differ only by case, such as `Example.com` and `example.com`, the migration that adds this rule stops and lists the colliding zones. That migration makes no changes to the database, and it can be run again once the collisions are resolved.

### Before Upgrading to 3.x

Upgrade to version 2.3.1 first, then run the **Check DNS Zone Name Collisions** job from **Jobs > Jobs**, in the **DNS** group. The job doesn't change any data, it just logs a warning for each DNS view with colliding zones:

```no-highlight
View "Default": "Example.com" (12 record(s)), "example.com" (0 record(s))
Rename, merge, or delete the colliding zones before upgrading.
```

Resolve the collisions (see below) and run the job again until it reports `No DNS zone name collisions found.`, then upgrade to 3.0.

### After Installing 3.0

To find collisions after installing the new version of the package, run the following command before running `nautobot-server post_upgrade`. The command does not require the new migration to be applied:

```no-highlight
nautobot-server check_dns_zone_name_collisions
```

The command exits with a non-zero status when collisions exist and lists each colliding zone with its ID and the number of DNS records it contains:

```no-highlight
Found 1 group(s) of DNS zones whose names differ only by letter case within the same DNS view.
    View "Default": "Example.com" (ID 0f8a0670-459b-430f-8c5e-a631888509d4, 12 record(s)), "example.com" (ID 1318ebef-499a-4f7f-b360-15da9b056b63, 0 record(s))
CommandError: Rename, merge, or delete the colliding zones before upgrading.
```

Resolve each collision by renaming the zone, moving it to another DNS view, or moving its records to the zone you keep and deleting the other. Then run the command again until it reports `No DNS zone name collisions found.`, and run `nautobot-server post_upgrade`.
