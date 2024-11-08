"""Template code for the records table."""

DNS_RECORDS_TYPE = """{% load helpers %}
        {% with record_model=record|meta:"model_name" %}
            {{ record | meta:"verbose_name" | split:" " | first}}
        {% endwith %}
"""

DNS_RECORDS_NAME = """{% load helpers %}
        {{ record | hyperlinked_object}}
"""

DNS_RECORDS_VALUE = """{% load helpers %}
        {% with record_model=record|meta:"model_name" %}
            {% if record_model in "arecordmodel,aaaarecordmodel" %}
                {{ record.address }}
            {% elif record_model in "nsrecordmodel" %}
                {{ record.server }}
            {% elif record_model in "cnamerecordmodel" %}
                {{ record.alias }}
            {% elif record_model in "mxrecordmodel" %}
                {{ record.mail_server }}
            {% elif record_model in "txtrecordmodel" %}
                {{ record.text }}
            {% elif record_model in "ptrrecordmodel" %}
                {{ record.ptrdname }}
            {% endif %}
        {% endwith %}
"""

DNS_RECORDS_ACTIONS = """{% load helpers %}
        {% load dns_tags %}
        {% with record_model=record|meta:"model_name" %}
            {% if perms.nautobot_dns_models.change_dnszonemodel %}
                {% if request.user|user_has_change_access:record %}
                    <a href="{{ record|url_with_action:"edit" }}" class="btn btn-xs btn-warning" title="Edit">
                        <i class="mdi mdi-pencil"></i>
                    </a>
                {% endif %}
                {% if request.user|user_has_delete_access:record %}
                    <a href="{{ record|url_with_action:'delete'  }}" class="btn btn-xs btn-danger" title="Delete">
                        <i class="mdi mdi-trash-can-outline"></i>
                    </a>
                {% endif %}
            {% endif %}
        {% endwith %}
"""

# DNS_RECORDS_ACTIONS = """{% load helpers %}
#         {% load dns_tags %}
#         {% with record_model=record|meta:"model_name" %}
#             {% if perms.nautobot_dns_models.change_dnszonemodel %}
#                 {% if perms.nautobot_dns_models.change_record_model %}
#                     <a href="{{ record|url_with_action:"edit" }}" class="btn btn-xs btn-warning" title="Edit">
#                         <i class="mdi mdi-pencil"></i>
#                     </a>
#                 {% endif %}
#                 {% if perms.nautobot_dns_models.delete_record_model %}
#                     <a href="{{ record|url_with_action:'delete'  }}" class="btn btn-xs btn-danger" title="Delete">
#                         <i class="mdi mdi-trash-can-outline"></i>
#                     </a>
#                 {% endif %}
#             {% endif %}
#         {% endwith %}
# """
