"""Data Validation Engine rules for nautobot_dns_models.

Registered automatically through `NautobotAppConfig.custom_validators`, so each rule runs on every
`full_clean()` of its model and is listed under Data Compliance for auditing existing records.
"""

from constance import config as constance_config
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.template.defaultfilters import truncatechars
from nautobot.apps.models import ComplianceError, DataComplianceRule
from nautobot.data_validation.models import DataCompliance

from nautobot_dns_models.models import (
    TXT_CHARACTER_STRING_MAX_OCTETS,
    TXT_RDATA_MAX_OCTETS,
    split_txt_character_strings,
    txt_wire_rdata_length,
)


class TXTRecordRFC1035LengthRule(DataComplianceRule):
    """Validate TXT RDATA lengths per RFC 1035 §3.3.14.

    - each <character-string> is at most 255 octets (RFC 1035 §3.3)
    - total RDATA is at most 65535 octets, counting the length octet that prefixes each string

    Enforced (blocks the save) when `DNS_VALIDATION_LEVEL` is "wire-format"; otherwise the result is only
    recorded as Data Compliance, so non-compliant records can still be found and fixed.
    """

    name = "TXT Record RFC 1035 Length"
    model = "nautobot_dns_models.txtrecord"

    def __init__(self, obj):
        """Derive enforcement from the app's validation level.

        Set per instance rather than as a property: the Data Compliance job assigns `enforce = False` to
        run rules in audit-only mode.
        """
        super().__init__(obj)
        # Kept directly: the validator context key is "object" in Nautobot 3.1 and "obj" from 3.2 onward.
        self.txt_record = obj
        self.enforce = getattr(constance_config, "nautobot_dns_models__DNS_VALIDATION_LEVEL") == "wire-format"

    def audit(self):
        """Raise a ComplianceError on `text` if any RFC 1035 length limit is exceeded."""
        text = self.txt_record.text

        try:
            character_string_list = split_txt_character_strings(text)
        except ValidationError as error:
            # Presentation-format parse errors (e.g. an unterminated quote) are compliance failures too, so
            # they follow the same enforce/audit behavior as the length checks.
            raise ComplianceError(error.message_dict) from error

        for position, character_string in enumerate(character_string_list, start=1):
            octets = len(character_string.encode("utf-8"))
            if octets > TXT_CHARACTER_STRING_MAX_OCTETS:
                raise ComplianceError(
                    {
                        "text": (
                            f"Character-string {position} is {octets} bytes (octets); the maximum is "
                            f"{TXT_CHARACTER_STRING_MAX_OCTETS}. Split the value into multiple "
                            'double-quoted character-strings, e.g. "part one" "part two".'
                        )
                    }
                )

        wire_length = txt_wire_rdata_length(character_string_list)
        if wire_length > TXT_RDATA_MAX_OCTETS:
            raise ComplianceError(
                {
                    "text": (
                        f"Total TXT record data is {wire_length} bytes (octets) in wire format; "
                        f"the maximum is {TXT_RDATA_MAX_OCTETS}."
                    )
                }
            )

    def compliance_result(self, message, attribute=None, valid=True):
        """Record a DataCompliance result, truncating the stored attribute value to fit its column.

        Mirrors `DataComplianceRule.compliance_result()`, which stores the raw value in a 255-character
        column: TXT content can be up to 65535 octets, and the values that fail this rule are the long ones.
        """
        attribute_value = ""
        if attribute:
            max_length = DataCompliance._meta.get_field("validated_attribute_value").max_length
            attribute_value = truncatechars(str(getattr(self.txt_record, attribute) or ""), max_length)
        else:
            attribute = "__all__"
        result, _ = DataCompliance.objects.update_or_create(
            compliance_class_name=self.name,
            content_type=ContentType.objects.get_for_model(self.txt_record),
            object_id=self.txt_record.id,
            validated_attribute=attribute,
            defaults={
                "last_validation_date": self.result_date,
                "validated_object_str": str(self.txt_record),
                "validated_attribute_value": attribute_value,
                "message": message,
                "valid": valid,
            },
        )
        result.validated_save()


custom_validators = [TXTRecordRFC1035LengthRule]
