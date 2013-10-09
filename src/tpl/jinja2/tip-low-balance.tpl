{% set user = a._FROM_USER._NAME %}
{% set balance_fmt = "%.6g %s" % (balance, a._COIN) %}
I'm sorry {{ user }}, your _{{ action_name }}_ balance of __{{ balance_fmt }}__ is insufficient for this {{ action_name }}.
{% if action_name == 'withdraw' %}
Withdrawals are subject to network fees and network confirmation times. See help for details.
{% endif %}
