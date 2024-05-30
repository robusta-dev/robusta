.. _sinks-overview:

Integrating Sinks
==========================

Robusta can send notifications to various destinations, called sinks. These are general settings for all sinks, please take a look at the specific sink guide for detailed instructions.

For a list of all sinks, refer to :ref:`Sinks Reference`.

Defining Sinks
^^^^^^^^^^^^^^^^^^
Sinks are defined in Robusta's Helm chart, using the ``sinksConfig`` value:

.. code-block:: yaml

    sinksConfig:
    - ms_teams_sink:                  # sink type
        name: my_teams_sink           # arbitrary name
        webhook_url: <placeholder>    # a sink-specific parameter
        stop: false                   # optional (see `Routing Alerts to only one Sink`)
        scope: {}                     # optional routing rules
        match: {}                     # optional routing rules (deprecated; see below)
        default: true                 # optional (see below)

To add a sink, update ``sinksConfig`` according to the instructions in :ref:`Sinks Reference`. Then do a :ref:`Helm Upgrade <Simple Upgrade>`.

Integrate as many sinks as you like.

.. _sink-matchers:

Routing Alerts to Only One Sink
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, alerts are sent to all sinks that matches the alerts.

To prevent sending alerts to more sinks after the current one, you can specify ``stop: true``

The sinks evaluation order, is the order defined in ``generated_values.yaml``.

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: production_sink
        slack_channel: production-notifications
        api_key: secret-key
        scope:
          include:
            - namespace: production
        stop: true

.. _sink-scope-matching:

Routing Alerts To Specific Sinks
***************************************

Define which messages a sink accepts using ``scope``.

For example, **Slack**  can be integrated to receive high-severity messages in a specific namespace. Other messages will not be sent to this **Slack** sink.

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        scope:
          include: # more options available - see below
            - namespace: [prod]
              severity: HIGH

Each attribute expression used in the ``scope`` specification can be 1 item, or a list, where each is either a regex or an exact match

``Scope`` allows specifying a set of ``include`` and ``exclude`` sections:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        scope:
        # AND between namespace and labels, but OR within each selector
          include:
            - namespace: default
              labels: "instance=1,foo!=x.*"
            - namespace: bla
              name:
              - foo
              - qux
          exclude:
            - type: ISSUE
              title: .*crash.*
            - name: bar[a-z]*


In order for a message to be sent to a ``Sink``, it must match **one of** the ``include`` sections, and **must not** match **all** the ``exclude`` sections.

When multiple attributes conditions are present, all must be satisfied.

The following attributes can be included in an ``include``/``excluded`` block:

- ``title``: e.g. ``Crashing pod foo in namespace default``
- ``name`` : the Kubernetes object name
- ``namespace``: the Kubernetes object namespace
- ``namespace_labels``: labels assigned to the namespace; matching these is done in the same way as matching ``labels`` (see below)
- ``node`` : the Kubernetes node name
- ``severity``: one of ``INFO``, ``LOW``, ``MEDIUM``, ``HIGH``
- ``type``: one of ``ISSUE``, ``CONF_CHANGE``, ``HEALTH_CHECK``, ``REPORT``
- ``kind``: one of ``deployment``, ``node``, ``pod``, ``job``, ``daemonset``
- ``source``: one of ``NONE``, ``KUBERNETES_API_SERVER``, ``PROMETHEUS``, ``MANUAL``, ``CALLBACK``
- ``identifier``: e.g. ``CrashLoopBackoff``
- ``labels``: A comma separated list of ``key=val`` e.g. ``foo=bar,instance=123``
- ``annotations``: A comma separated list of ``key=val`` e.g. ``app.kubernetes.io/name=prometheus``

.. note::

    ``labels`` and ``annotations`` are both the Kubernetes resource labels and annotations
    (e.g. pod labels) and the Prometheus alert labels and annotations. If both contains the
    same label/annotation, the value from the Prometheus alert is preferred.

.. note::

    For performance reasons, the namespace information used for matching ``namespace_labels``
    is cached (with a default cache timeout of 30 minutes). If you change namespace labels
    and want these changes to be immediately reflected in the sink ``scope`` matching
    mechanism, you will need to manually restart the Robusta runner.

.. details:: How do I find the ``identifier`` value to use in a match block? (deprecated)

    For Prometheus alerts, it's always the alert name.

    .. TODO: update after we finish our improvements here:
    .. For builtin APIServer alerts, it can vary, but common values are ``CrashLoopBackoff``, ``ImagePullBackoff``, ``ConfigurationChange/KubernetesResource/Change``, and ``JobFailure``.

    For custom playbooks, it's the value you set in :ref:`create_finding<create_finding>` under ``aggregation_key``.

    Ask us in Slack if you need help.

By default, every message is sent to every matching sink. To change this behaviour, you can mark a sink as :ref:`non-default <Non-default sinks>`.

The top-level mechanism works as follows:

#. If the notification is **excluded** by any of the sink ``scope`` excludes - drop it
#. If the notification is **included** by any of the sink ``scope`` includes - accept it
#. If the notification is **included** by any of the sink ``matchers`` - accept it (Deprecated)

Any of (but not both) of the ``include`` and ``exclude`` may be left undefined or empty.
An undefined/empty ``include`` section will effectively allow all alerts, and an
undefined/empty ``exclude`` section will not exclude anything.

Inside the ``include`` and ``exclude`` section, at the topmost level, the consecutive
items act with the OR logic, meaning that it's enough to match a single item in the
list in order to allow/reject a message. The same applies to the items listed under
each attribute name.

Within a specific ``labels`` or ``annotations`` expression, the logic is ``AND``

.. code-block:: yaml

    ....
        scope:
          include:
            - labels: "instance=1,foo=x.*"
    .....

The above requires that the ``instance`` will have a value of ``1`` **AND** the ``foo`` label values starts with ``x``

Match Section (Deprecated)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Define which messages a sink accepts using *matchers*.

For example, Slack can be integrated to receive high-severity messages in a specific
namespace. Other messages will not be sent to Slack.

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: test_sink
        slack_channel: test-notifications
        api_key: secret-key
        match:
          namespace: [prod]
          severity: [HIGH]
          # more options available - see below

When multiple match conditions are present, all must be satisfied.

The following attributes can be included in a *match* block:

- ``title``: e.g. ``Crashing pod foo in namespace default``
- ``name`` : the Kubernetes object name
- ``namespace``: the Kubernetes object namespace
- ``node`` : the Kubernetes node name
- ``severity``: one of ``INFO``, ``LOW``, ``MEDIUM``, ``HIGH``
- ``type``: one of ``ISSUE``, ``CONF_CHANGE``, ``HEALTH_CHECK``, ``REPORT``
- ``kind``: one of ``deployment``, ``node``, ``pod``, ``job``, ``daemonset``
- ``source``: one of ``NONE``, ``KUBERNETES_API_SERVER``, ``PROMETHEUS``, ``MANUAL``, ``CALLBACK``
- ``identifier``: e.g. ``CrashLoopBackoff``
- ``labels``: A comma separated list of ``key=val`` e.g. ``foo=bar,instance=123``
- ``annotations``: A comma separated list of ``key=val`` e.g. ``app.kubernetes.io/name=prometheus``

.. note::

    ``labels`` and ``annotations`` are both the Kubernetes resource labels and annotations
    (e.g. pod labels) and the Prometheus alert labels and annotations. If both contains the
    same label/annotation, the value from the Prometheus alert is preferred.


.. details:: How do I find the ``identifier`` value to use in a match block? (deprecated)

    For Prometheus alerts, it's always the alert name.

    .. TODO: update after we finish our improvements here:
    .. For builtin APIServer alerts, it can vary, but common values are ``CrashLoopBackoff``, ``ImagePullBackoff``, ``ConfigurationChange/KubernetesResource/Change``, and ``JobFailure``.

    For custom playbooks, it's the value you set in :ref:`create_finding<create_finding>` under ``aggregation_key``.

    Ask us in Slack if you need help.

By default, every message is sent to every matching sink. To change this behaviour, you can mark a sink as :ref:`non-default <Non-default sinks>`.

Match Section (Deprecated): Matches Can Be Lists or Regexes
***********************************************************

*match* rules support both regular expressions and lists of exact values:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        # AND between namespace and severity
        match:
          namespace: ^prod$                # match the "prod" namespace exactly
          severity: [HIGH, LOW]            # either HIGH or LOW (OR logic)

Regular expressions must be in `Python re module format <https://docs.python.org/3/library/re.html#regular-expression-syntax>`_, as passed to `re.match <https://docs.python.org/3/library/re.html#re.match>`_.

Match Section (Deprecated): Matching Labels and Annotations
***********************************************************

Special syntax is used for matching labels and annotations:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        match:
          labels: "foo=bar,instance=123"   # both labels must match

The syntax is similar to Kubernetes selectors, but only `=` conditions are allowed, not `!=`

Match Section (Deprecated): Or Between Matches
**********************************************

You can use `Or` between *match* rules:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: prod_slack_sink
        slack_channel: prod-notifications
        api_key: secret-key
        # AND between namespace and labels, but or within each selector
        match:
          namespace:
          - default
          - robusta
          labels:
          - "instance=123"
          - "instance=456"

The above will match a resource from namespace (default *or* robusta) *and* label (instance=123 *or* instance=456)

Alternative Routing Methods
************************************************

For :ref:`customPlaybooks <defining-playbooks>`, there is another option for routing notifications.

Instead of using sink matchers, you can set the *sinks* attribute per playbook:

.. code-block:: yaml

    customPlaybooks:
    - triggers:
      - on_job_failure: {}
      actions:
      - create_finding:
          aggregation_key: "JobFailure"
          title: "Job Failed"
      - job_info_enricher: {}
      - job_events_enricher: {}
      - job_pod_enricher: {}
      sinks:
        - "some_sink"
        - "some_other_sink"

Notifications generated this way are sent exclusively to the specified sinks. They will still be filtered by matchers.

Non-Default Sinks
*********************************

To prevent a sink from receiving most notifications, you can set ``default: false``. In this case, notifications will be
routed to the sink only from :ref:`customPlaybooks that explicitly name this sink <Alternative Routing Methods>`.

Here too, matchers apply as usual and perform further filtering.

Time-limiting sink activity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible, for any sink, to set the schedule of its activation by specifying the ``activity`` field in its
configuration. You can specify multiple time spans, with specific days of the week and hours in these days that
the sink will be active. Outside of these specified time spans, the sink will not run - so for example Slack
messages will not be delivered.

An example of such a configuration is presented below:

.. code-block:: yaml

    sinksConfig:
    - slack_sink:
        name: main_slack_sink
        slack_channel: robusta-notifications
        api_key: xoxb-your-slack-key
        activity:
          timezone: CET
          intervals:
          - days: ['mon', 'tue', 'sun']
            hours:
            - start: 10:00
              end: 11:00
            - start: 16:00
              end: 17:00
          - days: ['thr']
            hours:
            - start: 10:00
              end: 16:00
            - start: 16:05
              end: 23:00

Note that if the ``activity`` field is omitted, it is assumed that the sink will always be activated.
As seen above, each section under ``intervals`` may have multiple spans of time under the ``hours``
key. If the ``hours`` section is omitted for a given interval, it's assumed that the sink will be
active for all the specified days, irrespective of time.

.. details:: Supported Timezones

    .. code-block::

      Africa/Abidjan
      Africa/Accra
      Africa/Addis_Ababa
      Africa/Algiers
      Africa/Asmara
      Africa/Asmera
      Africa/Bamako
      Africa/Bangui
      Africa/Banjul
      Africa/Bissau
      Africa/Blantyre
      Africa/Brazzaville
      Africa/Bujumbura
      Africa/Cairo
      Africa/Casablanca
      Africa/Ceuta
      Africa/Conakry
      Africa/Dakar
      Africa/Dar_es_Salaam
      Africa/Djibouti
      Africa/Douala
      Africa/El_Aaiun
      Africa/Freetown
      Africa/Gaborone
      Africa/Harare
      Africa/Johannesburg
      Africa/Juba
      Africa/Kampala
      Africa/Khartoum
      Africa/Kigali
      Africa/Kinshasa
      Africa/Lagos
      Africa/Libreville
      Africa/Lome
      Africa/Luanda
      Africa/Lubumbashi
      Africa/Lusaka
      Africa/Malabo
      Africa/Maputo
      Africa/Maseru
      Africa/Mbabane
      Africa/Mogadishu
      Africa/Monrovia
      Africa/Nairobi
      Africa/Ndjamena
      Africa/Niamey
      Africa/Nouakchott
      Africa/Ouagadougou
      Africa/Porto-Novo
      Africa/Sao_Tome
      Africa/Timbuktu
      Africa/Tripoli
      Africa/Tunis
      Africa/Windhoek
      America/Adak
      America/Anchorage
      America/Anguilla
      America/Antigua
      America/Araguaina
      America/Argentina/Buenos_Aires
      America/Argentina/Catamarca
      America/Argentina/ComodRivadavia
      America/Argentina/Cordoba
      America/Argentina/Jujuy
      America/Argentina/La_Rioja
      America/Argentina/Mendoza
      America/Argentina/Rio_Gallegos
      America/Argentina/Salta
      America/Argentina/San_Juan
      America/Argentina/San_Luis
      America/Argentina/Tucuman
      America/Argentina/Ushuaia
      America/Aruba
      America/Asuncion
      America/Atikokan
      America/Atka
      America/Bahia
      America/Bahia_Banderas
      America/Barbados
      America/Belem
      America/Belize
      America/Blanc-Sablon
      America/Boa_Vista
      America/Bogota
      America/Boise
      America/Buenos_Aires
      America/Cambridge_Bay
      America/Campo_Grande
      America/Cancun
      America/Caracas
      America/Catamarca
      America/Cayenne
      America/Cayman
      America/Chicago
      America/Chihuahua
      America/Coral_Harbour
      America/Cordoba
      America/Costa_Rica
      America/Creston
      America/Cuiaba
      America/Curacao
      America/Danmarkshavn
      America/Dawson
      America/Dawson_Creek
      America/Denver
      America/Detroit
      America/Dominica
      America/Edmonton
      America/Eirunepe
      America/El_Salvador
      America/Ensenada
      America/Fort_Nelson
      America/Fort_Wayne
      America/Fortaleza
      America/Glace_Bay
      America/Godthab
      America/Goose_Bay
      America/Grand_Turk
      America/Grenada
      America/Guadeloupe
      America/Guatemala
      America/Guayaquil
      America/Guyana
      America/Halifax
      America/Havana
      America/Hermosillo
      America/Indiana/Indianapolis
      America/Indiana/Knox
      America/Indiana/Marengo
      America/Indiana/Petersburg
      America/Indiana/Tell_City
      America/Indiana/Vevay
      America/Indiana/Vincennes
      America/Indiana/Winamac
      America/Indianapolis
      America/Inuvik
      America/Iqaluit
      America/Jamaica
      America/Jujuy
      America/Juneau
      America/Kentucky/Louisville
      America/Kentucky/Monticello
      America/Knox_IN
      America/Kralendijk
      America/La_Paz
      America/Lima
      America/Los_Angeles
      America/Louisville
      America/Lower_Princes
      America/Maceio
      America/Managua
      America/Manaus
      America/Marigot
      America/Martinique
      America/Matamoros
      America/Mazatlan
      America/Mendoza
      America/Menominee
      America/Merida
      America/Metlakatla
      America/Mexico_City
      America/Miquelon
      America/Moncton
      America/Monterrey
      America/Montevideo
      America/Montreal
      America/Montserrat
      America/Nassau
      America/New_York
      America/Nipigon
      America/Nome
      America/Noronha
      America/North_Dakota/Beulah
      America/North_Dakota/Center
      America/North_Dakota/New_Salem
      America/Nuuk
      America/Ojinaga
      America/Panama
      America/Pangnirtung
      America/Paramaribo
      America/Phoenix
      America/Port-au-Prince
      America/Port_of_Spain
      America/Porto_Acre
      America/Porto_Velho
      America/Puerto_Rico
      America/Punta_Arenas
      America/Rainy_River
      America/Rankin_Inlet
      America/Recife
      America/Regina
      America/Resolute
      America/Rio_Branco
      America/Rosario
      America/Santa_Isabel
      America/Santarem
      America/Santiago
      America/Santo_Domingo
      America/Sao_Paulo
      America/Scoresbysund
      America/Shiprock
      America/Sitka
      America/St_Barthelemy
      America/St_Johns
      America/St_Kitts
      America/St_Lucia
      America/St_Thomas
      America/St_Vincent
      America/Swift_Current
      America/Tegucigalpa
      America/Thule
      America/Thunder_Bay
      America/Tijuana
      America/Toronto
      America/Tortola
      America/Vancouver
      America/Virgin
      America/Whitehorse
      America/Winnipeg
      America/Yakutat
      America/Yellowknife
      Antarctica/Casey
      Antarctica/Davis
      Antarctica/DumontDUrville
      Antarctica/Macquarie
      Antarctica/Mawson
      Antarctica/McMurdo
      Antarctica/Palmer
      Antarctica/Rothera
      Antarctica/South_Pole
      Antarctica/Syowa
      Antarctica/Troll
      Antarctica/Vostok
      Arctic/Longyearbyen
      Asia/Aden
      Asia/Almaty
      Asia/Amman
      Asia/Anadyr
      Asia/Aqtau
      Asia/Aqtobe
      Asia/Ashgabat
      Asia/Ashkhabad
      Asia/Atyrau
      Asia/Baghdad
      Asia/Bahrain
      Asia/Baku
      Asia/Bangkok
      Asia/Barnaul
      Asia/Beirut
      Asia/Bishkek
      Asia/Brunei
      Asia/Calcutta
      Asia/Chita
      Asia/Choibalsan
      Asia/Chongqing
      Asia/Chungking
      Asia/Colombo
      Asia/Dacca
      Asia/Damascus
      Asia/Dhaka
      Asia/Dili
      Asia/Dubai
      Asia/Dushanbe
      Asia/Famagusta
      Asia/Gaza
      Asia/Harbin
      Asia/Hebron
      Asia/Ho_Chi_Minh
      Asia/Hong_Kong
      Asia/Hovd
      Asia/Irkutsk
      Asia/Istanbul
      Asia/Jakarta
      Asia/Jayapura
      Asia/Jerusalem
      Asia/Kabul
      Asia/Kamchatka
      Asia/Karachi
      Asia/Kashgar
      Asia/Kathmandu
      Asia/Katmandu
      Asia/Khandyga
      Asia/Kolkata
      Asia/Krasnoyarsk
      Asia/Kuala_Lumpur
      Asia/Kuching
      Asia/Kuwait
      Asia/Macao
      Asia/Macau
      Asia/Magadan
      Asia/Makassar
      Asia/Manila
      Asia/Muscat
      Asia/Nicosia
      Asia/Novokuznetsk
      Asia/Novosibirsk
      Asia/Omsk
      Asia/Oral
      Asia/Phnom_Penh
      Asia/Pontianak
      Asia/Pyongyang
      Asia/Qatar
      Asia/Qostanay
      Asia/Qyzylorda
      Asia/Rangoon
      Asia/Riyadh
      Asia/Saigon
      Asia/Sakhalin
      Asia/Samarkand
      Asia/Seoul
      Asia/Shanghai
      Asia/Singapore
      Asia/Srednekolymsk
      Asia/Taipei
      Asia/Tashkent
      Asia/Tbilisi
      Asia/Tehran
      Asia/Tel_Aviv
      Asia/Thimbu
      Asia/Thimphu
      Asia/Tokyo
      Asia/Tomsk
      Asia/Ujung_Pandang
      Asia/Ulaanbaatar
      Asia/Ulan_Bator
      Asia/Urumqi
      Asia/Ust-Nera
      Asia/Vientiane
      Asia/Vladivostok
      Asia/Yakutsk
      Asia/Yangon
      Asia/Yekaterinburg
      Asia/Yerevan
      Atlantic/Azores
      Atlantic/Bermuda
      Atlantic/Canary
      Atlantic/Cape_Verde
      Atlantic/Faeroe
      Atlantic/Faroe
      Atlantic/Jan_Mayen
      Atlantic/Madeira
      Atlantic/Reykjavik
      Atlantic/South_Georgia
      Atlantic/St_Helena
      Atlantic/Stanley
      Australia/ACT
      Australia/Adelaide
      Australia/Brisbane
      Australia/Broken_Hill
      Australia/Canberra
      Australia/Currie
      Australia/Darwin
      Australia/Eucla
      Australia/Hobart
      Australia/LHI
      Australia/Lindeman
      Australia/Lord_Howe
      Australia/Melbourne
      Australia/NSW
      Australia/North
      Australia/Perth
      Australia/Queensland
      Australia/South
      Australia/Sydney
      Australia/Tasmania
      Australia/Victoria
      Australia/West
      Australia/Yancowinna
      Brazil/Acre
      Brazil/DeNoronha
      Brazil/East
      Brazil/West
      CET
      CST6CDT
      Canada/Atlantic
      Canada/Central
      Canada/Eastern
      Canada/Mountain
      Canada/Newfoundland
      Canada/Pacific
      Canada/Saskatchewan
      Canada/Yukon
      Chile/Continental
      Chile/EasterIsland
      Cuba
      EET
      EST
      EST5EDT
      Egypt
      Eire
      Etc/GMT
      Etc/GMT+0
      Etc/GMT+1
      Etc/GMT+10
      Etc/GMT+11
      Etc/GMT+12
      Etc/GMT+2
      Etc/GMT+3
      Etc/GMT+4
      Etc/GMT+5
      Etc/GMT+6
      Etc/GMT+7
      Etc/GMT+8
      Etc/GMT+9
      Etc/GMT-0
      Etc/GMT-1
      Etc/GMT-10
      Etc/GMT-11
      Etc/GMT-12
      Etc/GMT-13
      Etc/GMT-14
      Etc/GMT-2
      Etc/GMT-3
      Etc/GMT-4
      Etc/GMT-5
      Etc/GMT-6
      Etc/GMT-7
      Etc/GMT-8
      Etc/GMT-9
      Etc/GMT0
      Etc/Greenwich
      Etc/UCT
      Etc/UTC
      Etc/Universal
      Etc/Zulu
      Europe/Amsterdam
      Europe/Andorra
      Europe/Astrakhan
      Europe/Athens
      Europe/Belfast
      Europe/Belgrade
      Europe/Berlin
      Europe/Bratislava
      Europe/Brussels
      Europe/Bucharest
      Europe/Budapest
      Europe/Busingen
      Europe/Chisinau
      Europe/Copenhagen
      Europe/Dublin
      Europe/Gibraltar
      Europe/Guernsey
      Europe/Helsinki
      Europe/Isle_of_Man
      Europe/Istanbul
      Europe/Jersey
      Europe/Kaliningrad
      Europe/Kiev
      Europe/Kirov
      Europe/Lisbon
      Europe/Ljubljana
      Europe/London
      Europe/Luxembourg
      Europe/Madrid
      Europe/Malta
      Europe/Mariehamn
      Europe/Minsk
      Europe/Monaco
      Europe/Moscow
      Europe/Nicosia
      Europe/Oslo
      Europe/Paris
      Europe/Podgorica
      Europe/Prague
      Europe/Riga
      Europe/Rome
      Europe/Samara
      Europe/San_Marino
      Europe/Sarajevo
      Europe/Saratov
      Europe/Simferopol
      Europe/Skopje
      Europe/Sofia
      Europe/Stockholm
      Europe/Tallinn
      Europe/Tirane
      Europe/Tiraspol
      Europe/Ulyanovsk
      Europe/Uzhgorod
      Europe/Vaduz
      Europe/Vatican
      Europe/Vienna
      Europe/Vilnius
      Europe/Volgograd
      Europe/Warsaw
      Europe/Zagreb
      Europe/Zaporozhye
      Europe/Zurich
      GB
      GB-Eire
      GMT
      GMT+0
      GMT-0
      GMT0
      Greenwich
      HST
      Hongkong
      Iceland
      Indian/Antananarivo
      Indian/Chagos
      Indian/Christmas
      Indian/Cocos
      Indian/Comoro
      Indian/Kerguelen
      Indian/Mahe
      Indian/Maldives
      Indian/Mauritius
      Indian/Mayotte
      Indian/Reunion
      Iran
      Israel
      Jamaica
      Japan
      Kwajalein
      Libya
      MET
      MST
      MST7MDT
      Mexico/BajaNorte
      Mexico/BajaSur
      Mexico/General
      NZ
      NZ-CHAT
      Navajo
      PRC
      PST8PDT
      Pacific/Apia
      Pacific/Auckland
      Pacific/Bougainville
      Pacific/Chatham
      Pacific/Chuuk
      Pacific/Easter
      Pacific/Efate
      Pacific/Enderbury
      Pacific/Fakaofo
      Pacific/Fiji
      Pacific/Funafuti
      Pacific/Galapagos
      Pacific/Gambier
      Pacific/Guadalcanal
      Pacific/Guam
      Pacific/Honolulu
      Pacific/Johnston
      Pacific/Kanton
      Pacific/Kiritimati
      Pacific/Kosrae
      Pacific/Kwajalein
      Pacific/Majuro
      Pacific/Marquesas
      Pacific/Midway
      Pacific/Nauru
      Pacific/Niue
      Pacific/Norfolk
      Pacific/Noumea
      Pacific/Pago_Pago
      Pacific/Palau
      Pacific/Pitcairn
      Pacific/Pohnpei
      Pacific/Ponape
      Pacific/Port_Moresby
      Pacific/Rarotonga
      Pacific/Saipan
      Pacific/Samoa
      Pacific/Tahiti
      Pacific/Tarawa
      Pacific/Tongatapu
      Pacific/Truk
      Pacific/Wake
      Pacific/Wallis
      Pacific/Yap
      Poland
      Portugal
      ROC
      ROK
      Singapore
      Turkey
      UCT
      US/Alaska
      US/Aleutian
      US/Arizona
      US/Central
      US/East-Indiana
      US/Eastern
      US/Hawaii
      US/Indiana-Starke
      US/Michigan
      US/Mountain
      US/Pacific
      US/Samoa
      UTC
      Universal
      W-SU
      WET
      Zulu

.. details:: Supported Days

    .. code-block::

      Capital
        - MON
        - TUE
        - WED
        - THR
        - FRI
        - SAT
        - SUN

      Lowercase
        - mon
        - tue
        - wed
        - thr
        - fri
        - sat
        - sun

Examples
^^^^^^^^^^^

🎓 :ref:`Route Alerts By Namespace`

🎓 :ref:`Route Alerts By Type`

🎓 :ref:`Routing with Exclusion Rules`

See Also
^^^^^^^^^^^^

🔔 :ref:`All Sinks <Sinks Reference>`

🎓 :ref:`Silencing Alerts`
