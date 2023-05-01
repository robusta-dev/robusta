from dataclasses import InitVar, dataclass, field
from typing import List, Optional

from hikaru.meta import HikaruBase, HikaruDocumentBase, KubernetesException
from hikaru.model import ListMeta, NetworkingV1Api, ObjectMeta
from hikaru.utils import Response

from robusta.integrations.kubernetes.ingress.kubernetes_client.api_client import ApiClient


@dataclass
class IngressList(HikaruDocumentBase):
    r"""
    IngressList is a collection of Ingress.

    Full name: IngressList

    Attributes:
    items: Items is the list of Ingress.
    apiVersion: APIVersion defines the versioned schema of this representation of an
        object. Servers should convert recognized schemas to the latest internal value,
        and may reject unrecognized values. More info:
        https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#resources
    kind: Kind is a string value representing the REST resource this object represents.
        Servers may infer this from the endpoint the client submits requests to. Cannot be
        updated. In CamelCase. More info:
        https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#types-kinds
    metadata: Standard object's metadata. More info:
        https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#metadata
    """

    _version = "v1"
    items: List["Ingress"]
    apiVersion: Optional[str] = "networking.k8s.io/v1"
    kind: Optional[str] = "IngressList"
    metadata: Optional["ListMeta"] = None
    # noinspection PyDataclass
    client: InitVar[Optional[ApiClient]] = None

    @staticmethod
    def listIngressForAllNamespaces(
        allow_watch_bookmarks: Optional[bool] = None,
        continue_: Optional[str] = None,
        field_selector: Optional[str] = None,
        label_selector: Optional[str] = None,
        limit: Optional[int] = None,
        pretty: Optional[str] = None,
        resource_version: Optional[str] = None,
        resource_version_match: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        watch: Optional[bool] = None,
        client: ApiClient = None,
        async_req: bool = False,
    ) -> Response:
        r"""
        list or watch objects of kind Ingress

        operationID: listIngressForAllNamespaces
        path: /apis/networking.k8s.io/v1/ingresses

        :param allow_watch_bookmarks: allowWatchBookmarks requests watch events with
            type "BOOKMARK". Servers that do not implement bookmarks may ignore
            this flag and bookmarks are sent at the server's discretion. Clients
            should not assume bookmarks are returned at any specific interval,
            nor may they assume the server will send any BOOKMARK event during a
            session. If this is not a watch, this field is ignored. If the
            feature gate WatchBookmarks is not enabled in apiserver, this field
            is ignored.
        :param continue_: The continue option should be set when retrieving more
            results from the server. Since this value is server defined, clients
            may only use the continue value from a previous query result with
            identical query parameters (except for the value of continue) and
            the server may reject a continue value it does not recognize. If the
            specified continue value is no longer valid whether due to
            expiration (generally five to fifteen minutes) or a configuration
            change on the server, the server will respond with a 410
            ResourceExpired error together with a continue token. If the client
            needs a consistent list, it must restart their list without the
            continue field. Otherwise, the client may send another list request
            with the token received with the 410 error, the server will respond
            with a list starting from the next key, but from the latest
            snapshot, which is inconsistent from the previous list results -
            objects that are created, modified, or deleted after the first list
            request will be included in the response, as long as their keys are
            after the "next key". This field is not supported when watch is
            true. Clients may start a watch from the last resourceVersion value
            returned by the server and not miss any modifications.
        :param field_selector: A selector to restrict the list of returned objects by
            their fields. Defaults to everything.
        :param label_selector: A selector to restrict the list of returned objects by
            their labels. Defaults to everything.
        :param limit: limit is a maximum number of responses to return for a list call.
            If more items exist, the server will set the `continue` field on the
            list metadata to a value that can be used with the same initial
            query to retrieve the next set of results. Setting a limit may
            return fewer than the requested amount of items (up to zero items)
            in the event all requested objects are filtered out and clients
            should only use the presence of the continue field to determine
            whether more results are available. Servers may choose not to
            support the limit argument and will return all of the available
            results. If limit is specified and the continue field is empty,
            clients may assume that no more results are available. This field is
            not supported if watch is true. The server guarantees that the
            objects returned when using continue will be identical to issuing a
            single list call without a limit - that is, no objects created,
            modified, or deleted after the first request is issued will be
            included in any subsequent continued requests. This is sometimes
            referred to as a consistent snapshot, and ensures that a client that
            is using limit to receive smaller chunks of a very large result can
            ensure they see all possible objects. If objects are updated during
            a chunked list the version of the object that was present at the
            time the first list result was calculated is returned.
        :param pretty: If 'true', then the output is pretty printed.
        :param resource_version: resourceVersion sets a constraint on what resource
            versions a request may be served from. See
            https://kubernetes.io/docs/reference/using-api/api-concepts/#resource-versions
            for details. Defaults to unset
        :param resource_version_match: resourceVersionMatch determines how
            resourceVersion is applied to list calls. It is highly recommended
            that resourceVersionMatch be set for list calls where
            resourceVersion is set See
            https://kubernetes.io/docs/reference/using-api/api-concepts/#resource-versions
            for details. Defaults to unset
        :param timeout_seconds: Timeout for the list/watch call. This limits the
            duration of the call, regardless of any activity or inactivity.
        :param watch: Watch for changes to the described resources and return them as a
            stream of add, update, and remove notifications. Specify
            resourceVersion.
        :param client: optional; instance of kubernetes.client.api_client.ApiClient
        :param async_req: bool; if True, call is async and the caller must invoke
            .get() on the returned Response object. Default is False, which makes
            the call blocking.

        :return: hikaru.utils.Response[T] instance with the following codes and
            obj value types:
          Code  ObjType    Description
          -----------------------------
          200   IngressList    OK
          401   None    Unauthorized
        """
        client_to_use = client
        inst = NetworkingV1Api(api_client=client_to_use)
        the_method = getattr(inst, "list_ingress_for_all_namespaces_with_http_info")
        if the_method is None:  # pragma: no cover
            raise RuntimeError(
                "Unable to locate method "
                "list_ingress_for_all_namespaces_with_http_info "
                "on NetworkingV1Api; possible release mismatch?"
            )
        all_args = dict()
        all_args["allow_watch_bookmarks"] = allow_watch_bookmarks
        all_args["_continue"] = continue_
        all_args["field_selector"] = field_selector
        all_args["label_selector"] = label_selector
        all_args["limit"] = limit
        all_args["pretty"] = pretty
        all_args["resource_version"] = resource_version
        all_args["resource_version_match"] = resource_version_match
        all_args["timeout_seconds"] = timeout_seconds
        all_args["watch"] = watch
        all_args["async_req"] = async_req
        result = the_method(**all_args)
        codes_returning_objects = (200,)
        return Response(result, codes_returning_objects)

    @staticmethod
    def listNamespacedIngress(
        namespace: str,
        allow_watch_bookmarks: Optional[bool] = None,
        continue_: Optional[str] = None,
        field_selector: Optional[str] = None,
        label_selector: Optional[str] = None,
        limit: Optional[int] = None,
        resource_version: Optional[str] = None,
        resource_version_match: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        watch: Optional[bool] = None,
        pretty: Optional[str] = None,
        client: ApiClient = None,
        async_req: bool = False,
    ) -> Response:
        r"""
        list or watch objects of kind Ingress

        operationID: listNamespacedIngress
        path: /apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses

        :param namespace: namespace for the resource
        :param allow_watch_bookmarks: allowWatchBookmarks requests watch events with
            type "BOOKMARK". Servers that do not implement bookmarks may ignore
            this flag and bookmarks are sent at the server's discretion. Clients
            should not assume bookmarks are returned at any specific interval,
            nor may they assume the server will send any BOOKMARK event during a
            session. If this is not a watch, this field is ignored. If the
            feature gate WatchBookmarks is not enabled in apiserver, this field
            is ignored.
        :param continue_: The continue option should be set when retrieving more
            results from the server. Since this value is server defined, clients
            may only use the continue value from a previous query result with
            identical query parameters (except for the value of continue) and
            the server may reject a continue value it does not recognize. If the
            specified continue value is no longer valid whether due to
            expiration (generally five to fifteen minutes) or a configuration
            change on the server, the server will respond with a 410
            ResourceExpired error together with a continue token. If the client
            needs a consistent list, it must restart their list without the
            continue field. Otherwise, the client may send another list request
            with the token received with the 410 error, the server will respond
            with a list starting from the next key, but from the latest
            snapshot, which is inconsistent from the previous list results -
            objects that are created, modified, or deleted after the first list
            request will be included in the response, as long as their keys are
            after the "next key". This field is not supported when watch is
            true. Clients may start a watch from the last resourceVersion value
            returned by the server and not miss any modifications.
        :param field_selector: A selector to restrict the list of returned objects by
            their fields. Defaults to everything.
        :param label_selector: A selector to restrict the list of returned objects by
            their labels. Defaults to everything.
        :param limit: limit is a maximum number of responses to return for a list call.
            If more items exist, the server will set the `continue` field on the
            list metadata to a value that can be used with the same initial
            query to retrieve the next set of results. Setting a limit may
            return fewer than the requested amount of items (up to zero items)
            in the event all requested objects are filtered out and clients
            should only use the presence of the continue field to determine
            whether more results are available. Servers may choose not to
            support the limit argument and will return all of the available
            results. If limit is specified and the continue field is empty,
            clients may assume that no more results are available. This field is
            not supported if watch is true. The server guarantees that the
            objects returned when using continue will be identical to issuing a
            single list call without a limit - that is, no objects created,
            modified, or deleted after the first request is issued will be
            included in any subsequent continued requests. This is sometimes
            referred to as a consistent snapshot, and ensures that a client that
            is using limit to receive smaller chunks of a very large result can
            ensure they see all possible objects. If objects are updated during
            a chunked list the version of the object that was present at the
            time the first list result was calculated is returned.
        :param resource_version: resourceVersion sets a constraint on what resource
            versions a request may be served from. See
            https://kubernetes.io/docs/reference/using-api/api-concepts/#resource-versions
            for details. Defaults to unset
        :param resource_version_match: resourceVersionMatch determines how
            resourceVersion is applied to list calls. It is highly recommended
            that resourceVersionMatch be set for list calls where
            resourceVersion is set See
            https://kubernetes.io/docs/reference/using-api/api-concepts/#resource-versions
            for details. Defaults to unset
        :param timeout_seconds: Timeout for the list/watch call. This limits the
            duration of the call, regardless of any activity or inactivity.
        :param watch: Watch for changes to the described resources and return them as a
            stream of add, update, and remove notifications. Specify
            resourceVersion.
        :param pretty: If 'true', then the output is pretty printed.
        :param client: optional; instance of kubernetes.client.api_client.ApiClient
        :param async_req: bool; if True, call is async and the caller must invoke
            .get() on the returned Response object. Default is False, which makes
            the call blocking.

        :return: hikaru.utils.Response[T] instance with the following codes and
            obj value types:
          Code  ObjType    Description
          -----------------------------
          200   IngressList    OK
          401   None    Unauthorized
        """
        client_to_use = client
        inst = NetworkingV1Api(api_client=client_to_use)
        the_method = getattr(inst, "list_namespaced_ingress_with_http_info")
        if the_method is None:  # pragma: no cover
            raise RuntimeError(
                "Unable to locate method "
                "list_namespaced_ingress_with_http_info "
                "on NetworkingV1Api; possible release mismatch?"
            )
        all_args = dict()
        all_args["namespace"] = namespace
        all_args["allow_watch_bookmarks"] = allow_watch_bookmarks
        all_args["_continue"] = continue_
        all_args["field_selector"] = field_selector
        all_args["label_selector"] = label_selector
        all_args["limit"] = limit
        all_args["resource_version"] = resource_version
        all_args["resource_version_match"] = resource_version_match
        all_args["timeout_seconds"] = timeout_seconds
        all_args["watch"] = watch
        all_args["pretty"] = pretty
        all_args["async_req"] = async_req
        result = the_method(**all_args)
        codes_returning_objects = (200,)
        return Response(result, codes_returning_objects)


@dataclass
class Ingress(HikaruDocumentBase):
    r"""
    Ingress is a collection of rules that allow inbound connections to reach the endpoints
    defined by a backend. An Ingress can be configured to give services
    externally-reachable urls, load balance traffic, terminate SSL, offer name based
    virtual hosting etc.

    Full name: Ingress

    Attributes:
    apiVersion: APIVersion defines the versioned schema of this representation of an
        object. Servers should convert recognized schemas to the latest internal value,
        and may reject unrecognized values. More info:
        https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#resources
    kind: Kind is a string value representing the REST resource this object represents.
        Servers may infer this from the endpoint the client submits requests to. Cannot be
        updated. In CamelCase. More info:
        https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#types-kinds
    metadata: Standard object's metadata. More info:
        https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#metadata
    spec: Spec is the desired state of the Ingress. More info:
        https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#spec-and-status
    status: Status is the current state of the Ingress. More info:
        https://git.k8s.io/community/contributors/devel/sig-architecture/api-conventions.md#spec-and-status
    """

    _version = "v1"
    apiVersion: Optional[str] = "networking.k8s.io/v1"
    kind: Optional[str] = "Ingress"
    metadata: Optional["ObjectMeta"] = None
    spec: Optional["IngressSpec"] = None
    status: Optional["IngressStatus"] = None
    # noinspection PyDataclass
    client: InitVar[Optional[ApiClient]] = None

    @staticmethod
    def readNamespacedIngress(
        name: str,
        namespace: str,
        exact: Optional[bool] = None,
        export: Optional[bool] = None,
        pretty: Optional[str] = None,
        client: ApiClient = None,
        async_req: bool = False,
    ) -> Response:
        r"""
        read the specified Ingress

        operationID: readNamespacedIngress
        path: /apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses/{name}

        :param name: name for the resource
        :param namespace: namespace for the resource
        :param exact: Should the export be exact. Exact export maintains
            cluster-specific fields like 'Namespace'. Deprecated. Planned for
            removal in 1.18.
        :param export: Should this value be exported. Export strips fields that a user
            can not specify. Deprecated. Planned for removal in 1.18.
        :param pretty: If 'true', then the output is pretty printed.
        :param client: optional; instance of kubernetes.client.api_client.ApiClient
        :param async_req: bool; if True, call is async and the caller must invoke
            .get() on the returned Response object. Default is False, which makes
            the call blocking.

        :return: hikaru.utils.Response[T] instance with the following codes and
            obj value types:
          Code  ObjType    Description
          -----------------------------
          200   Ingress    OK
          401   None    Unauthorized
        """
        client_to_use = client
        inst = NetworkingV1Api(api_client=client_to_use)
        the_method = getattr(inst, "read_namespaced_ingress_with_http_info")
        if the_method is None:  # pragma: no cover
            raise RuntimeError(
                "Unable to locate method "
                "read_namespaced_ingress_with_http_info "
                "on NetworkingV1Api; possible release mismatch?"
            )
        all_args = dict()
        all_args["name"] = name
        all_args["namespace"] = namespace
        all_args["exact"] = exact
        all_args["export"] = export
        all_args["pretty"] = pretty
        all_args["async_req"] = async_req
        result = the_method(**all_args)
        codes_returning_objects = (200,)
        return Response(result, codes_returning_objects)

    def read(
        self,
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        exact: Optional[bool] = None,
        export: Optional[bool] = None,
        pretty: Optional[str] = None,
        client: ApiClient = None,
    ) -> "Ingress":
        r"""
            read the specified Ingress

            operationID: readNamespacedIngress
            path: /apis/networking.k8s.io/v1/namespaces/{namespace}/ingresses/{name}

            :param name: name for the resource. NOTE: if you leave out the name from the
                arguments you *must* have filled in the name attribute in the
                metadata for the resource!
            :param namespace: namespace for the resource. NOTE: if you leave out the
                namespace from the arguments you *must* have filled in the namespace
                attribute in the metadata for the resource!
            :param exact: Should the export be exact. Exact export maintains
                cluster-specific fields like 'Namespace'. Deprecated. Planned for
                removal in 1.18.
            :param export: Should this value be exported. Export strips fields that a user
                can not specify. Deprecated. Planned for removal in 1.18.
            :param pretty: If 'true', then the output is pretty printed.
            :param client: optional; instance of kubernetes.client.api_client.ApiClient
            :return: returns self; the state of self may be permuted with a returned
                HikaruDocumentBase object, whose values will be merged into self
        (if of the same type).
            :raises: KubernetesException. Raised only by the CRUD methods to signal
                that a return code of 400 or higher was returned by the underlying
                Kubernetes library.
        """

        # noinspection PyDataclass
        client = client or self.client

        if namespace is not None:
            effective_namespace = namespace
        elif not self.metadata or not self.metadata.namespace:
            raise RuntimeError(
                "There must be a namespace supplied in either " "the arguments to read() or in a " "Ingress's metadata"
            )
        else:
            effective_namespace = self.metadata.namespace

        if name is not None:
            effective_name = name
        elif not self.metadata or not self.metadata.name:
            raise RuntimeError(
                "There must be a name supplied in either " "the arguments to read() or in a " "Ingress's metadata"
            )
        else:
            effective_name = self.metadata.name
        res = self.readNamespacedIngress(
            name=effective_name,
            namespace=effective_namespace,
            exact=exact,
            export=export,
            pretty=pretty,
            client=client,
        )
        if not 200 <= res.code <= 299:
            raise KubernetesException("Kubernetes returned error " + str(res.code))
        if self.__class__.__name__ == res.obj.__class__.__name__:
            self.merge(res.obj, overwrite=True)
        return self

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, ex_traceback):
        passed = ex_type is None and ex_value is None and ex_traceback is None
        has_rollback = hasattr(self, "__rollback")
        if passed:
            try:
                self.update()
            except Exception:
                if has_rollback:
                    self.merge(getattr(self, "__rollback"), overwrite=True)
                    delattr(self, "__rollback")
                raise
        if has_rollback:
            if not passed:
                self.merge(getattr(self, "__rollback"), overwrite=True)
            delattr(self, "__rollback")
        return False


@dataclass
class IngressSpec(HikaruBase):
    r"""
    IngressSpec describes the Ingress the user wishes to exist.

    Full name: IngressSpec

    Attributes:
    defaultBackend: DefaultBackend is the backend that should handle requests that don't
        match any rule. If Rules are not specified, DefaultBackend must be specified. If
        DefaultBackend is not set, the handling of requests that do not match any of the
        rules will be up to the Ingress controller.
    ingressClassName: IngressClassName is the name of the IngressClass cluster resource.
        The associated IngressClass defines which controller will implement the resource.
        This replaces the deprecated `kubernetes.io/ingress.class` annotation. For
        backwards compatibility, when that annotation is set, it must be given precedence
        over this field. The controller may emit a warning if the field and annotation
        have different values. Implementations of this API should ignore Ingresses without
        a class specified. An IngressClass resource may be marked as default, which can be
        used to set a default value for this field. For more information, refer to the
        IngressClass documentation.
    rules: A list of host rules used to configure the Ingress. If unspecified, or no rule
        matches, all traffic is sent to the default backend.
    tls: TLS configuration. Currently the Ingress only supports a single TLS port, 443. If
        multiple members of this list specify different hosts, they will be multiplexed on
        the same port according to the hostname specified through the SNI TLS extension,
        if the ingress controller fulfilling the ingress supports SNI.
    """

    defaultBackend: Optional["IngressBackend"] = None
    ingressClassName: Optional[str] = None
    rules: Optional[List["IngressRule"]] = field(default_factory=list)
    tls: Optional[List["IngressTLS"]] = field(default_factory=list)


@dataclass
class IngressBackend(HikaruBase):
    r"""
    IngressBackend describes all endpoints for a given service and port.

    Full name: IngressBackend

    Attributes:
    resource: Resource is an ObjectRef to another Kubernetes resource in the namespace of
        the Ingress object. If resource is specified, a service.Name and service.Port must
        not be specified. This is a mutually exclusive setting with "Service".
    service: Service references a Service as a Backend. This is a mutually exclusive
        setting with "Resource".
    """

    resource: Optional["TypedLocalObjectReference"] = None
    service: Optional["IngressServiceBackend"] = None


@dataclass
class TypedLocalObjectReference(HikaruBase):
    r"""
    TypedLocalObjectReference contains enough information to let you locate the typed
    referenced object inside the same namespace.

    Full name: TypedLocalObjectReference

    Attributes:
    kind: Kind is the type of resource being referenced
    name: Name is the name of resource being referenced
    apiGroup: APIGroup is the group for the resource being referenced. If APIGroup is not
        specified, the specified Kind must be in the core API group. For any other
        third-party types, APIGroup is required.
    """

    kind: str
    name: str
    apiGroup: Optional[str] = None


@dataclass
class IngressServiceBackend(HikaruBase):
    r"""
    IngressServiceBackend references a Kubernetes Service as a Backend.

    Full name: IngressServiceBackend

    Attributes:
    name: Name is the referenced service. The service must exist in the same namespace as
        the Ingress object.
    port: Port of the referenced service. A port name or port number is required for a
        IngressServiceBackend.
    """

    name: str
    port: Optional["ServiceBackendPort"] = None


@dataclass
class ServiceBackendPort(HikaruBase):
    r"""
    ServiceBackendPort is the service port being referenced.

    Full name: ServiceBackendPort

    Attributes:
    name: Name is the name of the port on the Service. This is a mutually exclusive
        setting with "Number".
    number: Number is the numerical port number (e.g. 80) on the Service. This is a
        mutually exclusive setting with "Name".
    """

    name: Optional[str] = None
    number: Optional[int] = None


@dataclass
class IngressStatus(HikaruBase):
    r"""
    IngressStatus describe the current state of the Ingress.

    Full name: IngressStatus

    Attributes:
    loadBalancer: LoadBalancer contains the current status of the load-balancer.
    """

    loadBalancer: Optional["LoadBalancerStatus"] = None


@dataclass
class LoadBalancerStatus(HikaruBase):
    r"""
    LoadBalancerStatus represents the status of a load-balancer.

    Full name: LoadBalancerStatus

    Attributes:
    ingress: Ingress is a list containing ingress points for the load-balancer. Traffic
        intended for the service should be sent to these ingress points.
    """

    ingress: Optional[List["LoadBalancerIngress"]] = field(default_factory=list)


@dataclass
class LoadBalancerIngress(HikaruBase):
    r"""
    LoadBalancerIngress represents the status of a load-balancer ingress point: traffic
    intended for the service should be sent to an ingress point.

    Full name: LoadBalancerIngress

    Attributes:
    hostname: Hostname is set for load-balancer ingress points that are DNS based
        (typically AWS load-balancers)
    ip: IP is set for load-balancer ingress points that are IP based (typically GCE or
        OpenStack load-balancers)
    """

    hostname: Optional[str] = None
    ip: Optional[str] = None


@dataclass
class IngressRule(HikaruBase):
    r"""
    IngressRule represents the rules mapping the paths under a specified host to the
    related backend services. Incoming requests are first evaluated for a host match, then
    routed to the backend associated with the matching IngressRuleValue.

    Full name: IngressRule

    Attributes:
    host: Host is the fully qualified domain name of a network host, as defined by RFC
        3986. Note the following deviations from the "host" part of the URI as defined in
        RFC 3986: 1. IPs are not allowed. Currently an IngressRuleValue can only apply to
        the IP in the Spec of the parent Ingress. 2. The `:` delimiter is not respected
        because ports are not allowed. Currently the port of an Ingress is implicitly :80
        for http and :443 for https. Both these may change in the future. Incoming
        requests are matched against the host before the IngressRuleValue. If the host is
        unspecified, the Ingress routes all traffic based on the specified
        IngressRuleValue. Host can be "precise" which is a domain name without the
        terminating dot of a network host (e.g. "foo.bar.com") or "wildcard", which is a
        domain name prefixed with a single wildcard label (e.g. "*.foo.com"). The wildcard
        character '*' must appear by itself as the first DNS label and matches only a
        single label. You cannot have a wildcard label by itself (e.g. Host == "*").
        Requests will be matched against the Host field in the following way: 1. If Host
        is precise, the request matches this rule if the http host header is equal to
        Host. 2. If Host is a wildcard, then the request matches this rule if the http
        host header is to equal to the suffix (removing the first label) of the wildcard
        rule.
    http:
    """

    host: Optional[str] = None
    http: Optional["HTTPIngressRuleValue"] = None


@dataclass
class HTTPIngressRuleValue(HikaruBase):
    r"""
    HTTPIngressRuleValue is a list of http selectors pointing to backends. In the example:
    http://<host>/<path>?<searchpart> -> backend where where parts of the url correspond
    to RFC 3986, this resource will be used to match against everything after the last '/'
    and before the first '?' or '#'.

    Full name: HTTPIngressRuleValue

    Attributes:
    paths: A collection of paths that map requests to backends.
    """

    paths: List["HTTPIngressPath"]


@dataclass
class HTTPIngressPath(HikaruBase):
    r"""
    HTTPIngressPath associates a path with a backend. Incoming urls matching the path are
    forwarded to the backend.

    Full name: HTTPIngressPath

    Attributes:
    backend: Backend defines the referenced service endpoint to which the traffic will be
        forwarded to.
    path: Path is matched against the path of an incoming request. Currently it can
        contain characters disallowed from the conventional "path" part of a URL as
        defined by RFC 3986. Paths must begin with a '/'. When unspecified, all paths from
        incoming requests are matched.
    pathType: PathType determines the interpretation of the Path matching. PathType can be
        one of the following values: * Exact: Matches the URL path exactly. * Prefix:
        Matches based on a URL path prefix split by '/'. Matching is done on a path
        element by element basis. A path element refers is the list of labels in the path
        split by the '/' separator. A request is a match for path p if every p is an
        element-wise prefix of p of the request path. Note that if the last element of the
        path is a substring of the last element in request path, it is not a match (e.g.
        /foo/bar matches /foo/bar/baz, but does not match /foo/barbaz). *
        ImplementationSpecific: Interpretation of the Path matching is up to the
        IngressClass. Implementations can treat this as a separate PathType or treat it
        identically to Prefix or Exact path types. Implementations are required to support
        all path types.
    """

    backend: "IngressBackend"
    path: Optional[str] = None
    pathType: Optional[str] = None


@dataclass
class IngressTLS(HikaruBase):
    r"""
    IngressTLS describes the transport layer security associated with an Ingress.

    Full name: IngressTLS

    Attributes:
    secretName: SecretName is the name of the secret used to terminate TLS traffic on port
        443. Field is left optional to allow TLS routing based on SNI hostname alone. If
        the SNI host in a listener conflicts with the "Host" header field used by an
        IngressRule, the SNI host is used for termination and value of the Host header is
        used for routing.
    hosts: Hosts are a list of hosts included in the TLS certificate. The values in this
        list must match the name/s used in the tlsSecret. Defaults to the wildcard host
        setting for the loadbalancer controller fulfilling this Ingress, if left
        unspecified.
    """

    secretName: Optional[str] = None
    hosts: Optional[List[str]] = field(default_factory=list)
