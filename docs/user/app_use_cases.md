# Using the App

This document describes common use-cases and scenarios for this App.

## General Usage

Generally, this App is to used to keep track of DNS Zones and their related data and records. The idea is to have a set of models that can either be used to directly model DNS configurations or as a place to aggregate data about DNS related configuration from other tools. While A, AAAA, and PTR records are already partially supported within Nautobot core models, this App is meant to expand the type of DNS records and formalize DNS models within Nautobot.

## Use-cases and common workflows

Use the API or GUI to add DNS Zones and Record objects to Nautobot.

### Catalog Zones

+++ 2.4.0

A secondary name server has to be told which zones to serve, and that list is usually kept in each server's own configuration. A catalog zone, defined by [RFC 9432](https://datatracker.ietf.org/doc/html/rfc9432), holds that list as DNS data, so it can be kept in one place. This app maintains the catalog's contents in Nautobot; it does not serve the catalog or configure name servers, so publishing it is the job of whatever integration reads the data.

Create the catalog as a DNS zone with a Type of `Catalog`, then add the zones it should list: from the catalog's Member Zones panel, from the zone list's Add to Catalog action, from each zone's own form, or for a selection of zones through bulk edit. The same places remove a zone from its catalog. See [Catalog Zones](catalog_zones.md) for the records a catalog holds and the rules membership follows.

## Screenshots

### Primary Zone

![Adding a Primary DNS Zone](../images/getting_started-add-zone-3-light.png#only-light){ .on-glb }
![Adding a Primary DNS Zone](../images/getting_started-add-zone-3-dark.png#only-dark){ .on-glb }
[//]: # "`https://next.demo.nautobot.com/plugins/dns/dns-zones/add/`"

/// caption
Adding a Primary DNS Zone
///

![Primary DNS Zone View](../images/getting_started-add-record-3-light.png#only-light){ .on-glb }
![Primary DNS Zone View](../images/getting_started-add-record-3-dark.png#only-dark){ .on-glb }

/// caption
The Primary DNS Zone View
///

### Catalog Zone

![Adding a Catalog Zone](../images/use_cases-add-catalog-zone-1-light.png#only-light){ .on-glb }
![Adding a Catalog Zone](../images/use_cases-add-catalog-zone-1-dark.png#only-dark){ .on-glb }

/// caption
Adding a Catalog Zone
///

![Catalog Zone View](../images/use_cases-catalog-member-zones-light.png#only-light){ .on-glb }
![Catalog Zone View](../images/use_cases-catalog-member-zones-dark.png#only-dark){ .on-glb }

/// caption
The Catalog Zone View
///
