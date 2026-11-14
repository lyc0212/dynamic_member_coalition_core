"""Exact, non-owning accounting for the frozen append-only four-root graph.

This is deliberately not a general heap monitor.  The owner must use the frozen
mutation paths; arbitrary writes which bypass that owner are outside the proof.
No cache, scientific evaluator, comparator, or numerical kernel is imported here.
"""
import sys
import types
import weakref


class MeterError(RuntimeError):
    # Only errors originating in this new accounting boundary have this flag.
    # An ordinary original persistence-callback exception keeps legacy cleanup.
    skip_cache_logging_close = True
    def __init__(self, code, message=None, *, details=None):
        self.code = code
        self.details = {} if details is None else details
        super().__init__(message or code)


def _require(test, code='UNSUPPORTED_OWNED_GRAPH_MUTATION', message=None):
    if not test:
        raise MeterError(code, message)


def _kind(value):
    return 1 if type(value) is dict else 2 if type(value) is list else 3 if type(value) is tuple else 0


def metadata_body_size(value, *, roots=False):
    """One explicitly requested metadata-body sample, never a target-graph walk."""
    seen = set()
    def visit(item):
        token = id(item)
        if token in seen:
            return 0
        seen.add(token)
        amount = sys.getsizeof(item)
        if type(item) is dict:
            return amount + sum(visit(k) + visit(v) for k, v in item.items())
        if type(item) in (list, tuple, set, frozenset):
            return amount + sum(visit(v) for v in item)
        # weak references/callables are bodies, not invitations to follow owners,
        # globals, scientific arrays, or arbitrary __dict__ graphs.
        return amount
    return sum(visit(item) for item in value) if roots else visit(value)


def audit_detached_metadata(payload, source_ids):
    """Inspect actual persistent structures and closure cells, not declarations.

    The caller supplies source identities from its separately budgeted membership
    traversal. Runtime immortal atoms are allowed; ordinary strings/floats and
    containers are not. Function globals are not an ownership edge of a closure.
    """
    forbidden = set(source_ids)
    seen = set()
    inspected = 0
    def visit(value):
        nonlocal inspected
        token = id(value)
        if token in seen:
            return
        seen.add(token)
        inspected += 1
        immortal = value is None or value is True or value is False
        if not immortal and type(value) in (int, str, bytes, tuple):
            # CPython's immortal reference count is directly observed here; an
            # equal value, deepcopy, or guessed interned status is not a proof.
            immortal = sys.getrefcount(value) >= 1_000_000_000
        if token in forbidden and not immortal:
            raise MeterError('IDENTITY_LIFETIME_ASSURANCE_FAILED',
                             'Persistent metadata retains a measured source object')
        if isinstance(value, weakref.ReferenceType):
            return  # Never dereference an owner during a closure inspection.
        if type(value) is dict:
            for k, v in value.items():
                visit(k); visit(v)
        elif type(value) in (list, tuple, set, frozenset):
            for v in value:
                visit(v)
        elif isinstance(value, types.MethodType):
            visit(value.__self__); visit(value.__func__)
        elif isinstance(value, types.FunctionType):
            for cell in value.__closure__ or ():
                try: visit(cell.cell_contents)
                except ValueError: pass
            visit(value.__defaults__)
            visit(value.__kwdefaults__)
        elif not isinstance(value, (type, types.ModuleType, types.CodeType)):
            namespace = getattr(value, '__dict__', None)
            if namespace is not None:
                visit(namespace)
            for cls in type(value).__mro__:
                slots = cls.__dict__.get('__slots__', ())
                if type(slots) is str:
                    slots = (slots,)
                for name in slots:
                    if name not in ('__weakref__', '__dict__'):
                        try: visit(getattr(value, name))
                        except AttributeError: pass
    visit(payload)
    return {'passed': True, 'inspected_metadata_objects': inspected,
            'source_identity_count': len(forbidden),
            'scope': 'actual_payload_and_closures_no_function_globals_no_weakref_targets'}


class FourRootMeter:
    """Scope-local scalar ledger. Counted source objects are never retained.

    Only exact dict/list/tuple objects have outgoing edges. Each node records its
    weight once, with integer child-id multiplicities. Supported live nodes never
    disappear; a digest edge may disappear only when a trace retains the node.
    """
    def __init__(self, *, scope_id):
        self._scope_bytes = str(scope_id).encode('utf-8')
        self._nodes = {}
        self._incoming = {}
        self._roots = ()
        self._parts = {}
        self._current = 0
        self._peak = 0
        self._edges = 0
        self._sequence = 0
        self._trace_frontier = 0
        self._pending = 0
        self._unit_dirty = set()
        self._initializations = 0
        self._measurements = 0
        self._disposed = False

    def _add_edge(self, parent, child_id, count=1):
        edges = self._nodes[parent]['e']
        edges[child_id] = edges.get(child_id, 0) + count
        self._incoming[child_id] = self._incoming.get(child_id, 0) + count
        self._edges += count

    def _drop_edge(self, parent, child_id):
        node = self._nodes[parent]
        _require(node['e'].get(child_id, 0) > 0)
        _require(self._incoming.get(child_id, 0) > 1,
                 'LAST_ROOT_REFERENCE_REMOVAL_UNSUPPORTED')
        node['e'][child_id] -= 1
        if node['e'][child_id] == 0:
            del node['e'][child_id]
        self._incoming[child_id] -= 1
        self._edges -= 1

    def _register(self, value):
        token = id(value)
        if token in self._nodes:
            _require(self._nodes[token]['t'] == id(type(value)),
                     'IDENTITY_LIFETIME_ASSURANCE_FAILED')
            return token
        self._sequence += 1
        kind = _kind(value)
        node = {'g': self._sequence, 't': id(type(value)), 'k': kind,
                's': sys.getsizeof(value), 'e': {}, 'n': 0, 'tail': 0, 'pairs': {}}
        self._nodes[token] = node
        self._incoming.setdefault(token, 0)
        self._current += node['s']
        if kind == 1:
            for key, item in value.items():
                a, b = self._register(key), self._register(item)
                self._add_edge(token, a); self._add_edge(token, b)
                node['pairs'][a] = b
            node['n'] = len(value)
        elif kind in (2, 3):
            for item in value:
                self._add_edge(token, self._register(item))
            node['n'] = len(value)
            node['tail'] = 0 if not value else id(value[-1])
        return token

    def _refresh_shallow(self, value):
        node = self._nodes[id(value)]
        size = sys.getsizeof(value)
        self._current += size - node['s']
        node['s'] = size

    def _append_list(self, value):
        _require(type(value) is list)
        node = self._nodes[id(value)]
        previous = node['n']
        _require(len(value) >= previous)
        _require(not previous or id(value[previous - 1]) == node['tail'])
        for index in range(previous, len(value)):
            self._add_edge(id(value), self._register(value[index]))
        node['n'] = len(value)
        node['tail'] = 0 if not value else id(value[-1])
        self._refresh_shallow(value)

    def _append_dict(self, value, *, allow_prefix_replace=False):
        _require(type(value) is dict)
        node = self._nodes[id(value)]
        _require(len(value) >= node['n'])
        observed_keys = set()
        for key, item in value.items():
            key_id = id(key); observed_keys.add(key_id)
            old = node['pairs'].get(key_id)
            if old is None:
                self._add_edge(id(value), self._register(key))
                self._add_edge(id(value), self._register(item))
                node['pairs'][key_id] = id(item)
            elif old != id(item):
                _require(allow_prefix_replace and type(key) is str and key == 'prefix_digest')
                self._drop_edge(id(value), old)
                self._add_edge(id(value), self._register(item))
                node['pairs'][key_id] = id(item)
        _require(observed_keys.issuperset(node['pairs']))
        node['n'] = len(value)
        self._refresh_shallow(value)

    def _admit_roots(self, roots):
        _require(not self._disposed, 'IDENTITY_LIFETIME_ASSURANCE_FAILED')
        _require(type(roots) in (tuple, list) and len(roots) == 4)
        tokens = tuple(id(item) for item in roots)
        if not self._roots:
            for item in roots:
                token = self._register(item)
                self._incoming[token] = self._incoming.get(token, 0) + 1
            self._roots = tokens
            self._initializations += 1
            return True
        _require(tokens == self._roots)
        return False

    def _commit(self):
        self._peak = max(self._peak, self._current)
        self._measurements += 1
        self._pending = 0
        return self._current

    @staticmethod
    def _trace_witness(trace, digest_id, start=0):
        for index in range(start, len(trace)):
            row = trace[index]
            prefix = row.get('component_prefix_after') if type(row) is dict else None
            if type(prefix) is dict and id(prefix.get('prefix_digest')) == digest_id:
                return index
        return None

    def measure(self, owner):
        """Borrow four actual roots only within this synchronous call."""
        roots = (owner._components, owner._trace, owner._initial_positions, owner._targets)
        part = intervals = key = None
        try:
            first = self._admit_roots(roots)
            components, trace, initial, targets = roots
            _require(type(components) is dict and type(trace) is list and type(targets) is dict)
            if first:
                self._trace_frontier = len(trace)
            else:
                # Static roots and all existing descendants are frozen by the
                # owner contract; this is not arbitrary private-write detection.
                for static in (initial, targets):
                    _require(sys.getsizeof(static) == self._nodes[id(static)]['s'])
                self._append_list(trace)
                self._append_dict(components)
            for key, part in components.items():
                _require(type(key) is tuple and type(part) is dict)
                intervals = part.get('intervals')
                _require(type(intervals) is list and type(part.get('prefix_digest')) is str)
                token = id(key)
                digest_id = id(part['prefix_digest'])
                old = self._parts.get(token)
                if old is None:
                    witness = self._trace_witness(trace, digest_id, self._trace_frontier if not first else 0)
                    _require(witness is not None, 'IDENTITY_LIFETIME_ASSURANCE_FAILED')
                    self._parts[token] = {'p': id(part), 'l': id(intervals), 'd': digest_id, 'w': witness}
                else:
                    _require(id(part) == old['p'] and id(intervals) == old['l'])
                    if digest_id != old['d']:
                        previous = trace[old['w']].get('component_prefix_after')
                        _require(type(previous) is dict and id(previous.get('prefix_digest')) == old['d'],
                                 'IDENTITY_LIFETIME_ASSURANCE_FAILED')
                        witness = self._trace_witness(trace, digest_id, self._trace_frontier)
                        _require(witness is not None, 'IDENTITY_LIFETIME_ASSURANCE_FAILED')
                        self._append_dict(part, allow_prefix_replace=True)
                        old['d'] = digest_id; old['w'] = witness
                    else:
                        self._refresh_shallow(part)
                    self._append_list(intervals)
            self._trace_frontier = len(trace)
            return self._commit()
        finally:
            # No root, part, tuple key or interval handle crosses the boundary.
            roots = part = intervals = key = owner = None

    def measure_unit_graph(self, roots4, changes=()):
        """UNIT_ONLY explicit carriers. It never creates a cache or runs science."""
        try:
            first = self._admit_roots(roots4)
            if not first:
                _require({id(value) for value in changes} == self._unit_dirty)
                for value in changes:
                    _require(id(value) in self._nodes)
                    if type(value) is list:
                        self._append_list(value)
                    elif type(value) is dict:
                        self._append_dict(value, allow_prefix_replace=True)
                    else:
                        raise MeterError('UNSUPPORTED_OWNED_GRAPH_MUTATION')
            self._unit_dirty.clear()
            return self._commit()
        finally:
            roots4 = changes = None

    def controlled_transition(self, roots4, operation, container, key=None, value=None):
        """Pre-write boundary for declared UNIT_ONLY fixtures; no private proxy."""
        _require(tuple(id(item) for item in roots4) == self._roots)
        _require(id(container) in self._nodes)
        if operation == 'append':
            _require(type(container) is list and id(container) == self._roots[1])
            container.append(value)
        elif operation == 'dict_add':
            _require(type(container) is dict and id(container) == self._roots[0] and key not in container)
            container[key] = value
        elif operation == 'prefix_digest_replace':
            _require(type(container) is dict and key == 'prefix_digest' and key in container)
            old = container[key]
            _require(type(old) is str)
            _require(self._incoming.get(id(old), 0) > 1,
                     'LAST_ROOT_REFERENCE_REMOVAL_UNSUPPORTED')
            # The only permitted drop is retained by an immutable trace node.
            trace = roots4[1]
            _require(type(trace) is list and self._trace_witness(trace, id(old)) is not None,
                     'LAST_ROOT_REFERENCE_REMOVAL_UNSUPPORTED')
            _require(type(value) is str)
            container[key] = value
        else:
            raise MeterError('UNSUPPORTED_OWNED_GRAPH_MUTATION')
        self._pending += 1
        self._unit_dirty.add(id(container))

    def snapshot(self):
        return {'current_bytes': self._current, 'peak_bytes': self._peak,
                'node_count': len(self._nodes), 'edge_count': self._edges,
                'pending_update_count': self._pending,
                'measurement_count': self._measurements,
                'initialization_walks': self._initializations,
                'trace_frontier': self._trace_frontier,
                'scope_generation': self._scope_bytes.decode('utf-8'),
                'disposed': self._disposed,
                'value_scope': 'LAST_MEASURED_BEFORE_DISPOSAL' if self._disposed else 'ADMITTED_MEASUREMENT',
                'lifetime_scope': 'CONTROLLED_MONOTONE_ROOT_REACHABILITY'}

    def persistent_payload(self):
        return {'scope_bytes': self._scope_bytes, 'nodes': self._nodes,
                'incoming': self._incoming, 'root_ids': self._roots,
                'parts': self._parts, 'unit_dirty_ids': self._unit_dirty}

    def dispose(self):
        self._nodes.clear(); self._incoming.clear(); self._parts.clear()
        self._unit_dirty.clear(); self._pending = 0
        self._roots = (); self._scope_bytes = b''; self._edges = 0
        self._disposed = True
