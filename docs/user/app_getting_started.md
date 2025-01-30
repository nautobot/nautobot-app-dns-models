# Getting Started with the App

This document provides a step-by-step tutorial on how to get the App going and how to use it.

## Install the App

To install the App, please follow the instructions detailed in the [Installation Guide](../admin/install.md).

## First steps with the App

Navigate to the DNS Models under Apps in the navigation bar.

[](docs/images/icon-nautobot-dns-models.png)

The first step with the App is to create a DNS Zone. The Zone is the organizational container for DNS records. In our implementation, we have added the SoA record fields and details to the Zone, because a DNS Zone requires a single SoA record. The SoA fields are optional in case you are not recreating DNS server objects 1:1.

Create a DNS Zone by clicking the `+` button next to DNS Zones, or by clicking DNS Zones and clicking the Add Zone button at the top right.

Once the Zone is created, create the other records as necessary. Initially supported records include A, AAAA, CNAME, 

## What are the next steps?

You can check out the [Use Cases](app_use_cases.md) section for more examples.
