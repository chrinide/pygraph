"""
Implementing planarity testing as per "The Hopcroft-Tarjan Planarity Algorithm" by William Kocay
Location: http://www.combinatorialmath.ca/G&G/articles/planarity.pdf
"""

from collections import deque

from ..searching.depth_first_search import depth_first_search_with_parent_data


"""
In programming the Hopcroft-Tarjan algorithm one first begins with
the LowPtDFS in order to determine L1(v) and L2 (v). The adjacency lists
are then sorted by weight. Next, the BranchPtDFS can be executed in
order to establish the first node in Adj[u]. Then EmbedBranch is executed
in order to construct the lists LF and RF which determine the combina-
torial embedding of G. An alternative is to combine BranchPtDFS and
EmbedBranch into a single DFS, which is easy to do.
"""



def kocay_planarity_test(graph):
    """Determines whether a graph is planar."""

    # We first have to calculate the DFS-tree of the graph, so we can calculate the edge weights to determine
    # the order of embedding of the branches
    adj = __calculate_adjacency_lists(graph)
    dfs_data = __setup_dfs_data(graph, adj)

    # Now that we have enough information to sort the edges, we should do so and then recalculate the DFS tree
    adj = __sort_adjacency_lists(dfs_data)
    dfs_data = __setup_dfs_data(graph, adj)

    # We now have the information we need to calculate the branch points
    __branch_point_dfs(dfs_data)
    #b_u_lookup =__calculate_bu_dfs(dfs_data)
    #dfs_data['b_u_lookup'] = b_u_lookup

    # Now that everything is calculated and ordered, we can attempt to embed the graph
    is_planar = __embed_branch(dfs_data)

    return is_planar

def __setup_dfs_data(graph, adj):
    """Sets up the dfs_data object, for consistency."""
    dfs_data = __get_dfs_data(graph)

    dfs_data['graph'] = graph
    dfs_data['adj'] = adj

    L1, L2 = __low_point_dfs(dfs_data)
    dfs_data['lowpoint_1_lookup'] = L1
    dfs_data['lowpoint_2_lookup'] = L2

    edge_weights = __calculate_edge_weights(dfs_data)
    dfs_data['edge_weights'] = edge_weights

    return dfs_data


def __low_point_dfs(dfs_data):
    """Calculates the L1 and L2 for each vertex."""
    L1, L2 = __get_all_lowpoints(dfs_data)
    return (L1, L2)


def __calculate_edge_weights(dfs_data):
    """Calculates the weight of each edge, for embedding-order sorting."""
    graph = dfs_data['graph']

    weights = {}
    for edge_id in graph.get_all_edge_ids():
        edge_weight = __edge_weight(edge_id, dfs_data)
        weights[edge_id] = edge_weight

    return weights


def __sort_adjacency_lists(dfs_data):
    """Sorts the adjacency list representation by the edge weights."""
    new_adjacency_lists = {}

    adjacency_lists = dfs_data['adj']
    edge_weights = dfs_data['edge_weights']
    edge_lookup = dfs_data['edge_lookup']

    for node_id, adj_list in adjacency_lists.items():
        node_weight_lookup = {}
        frond_lookup = {}
        for node_b in adj_list:
            edge_id = dfs_data['graph'].get_first_edge_id_by_node_ids(node_id, node_b)
            node_weight_lookup[node_b] = edge_weights[edge_id]
            frond_lookup[node_b] = 1 if edge_lookup[edge_id] == 'backedge' else 2

        # Fronds should be before branches if the weights are equal
        new_list = sorted(adj_list, key=lambda n: frond_lookup[n])

        # Sort by weights
        new_list.sort(key=lambda n: node_weight_lookup[n])

        # Add the new sorted list to the new adjacency list lookup table
        new_adjacency_lists[node_id] = new_list

    return new_adjacency_lists


def __branch_point_dfs(dfs_data):
    """DFS that calculates the b(u) and N(u) lookups, and also reorders the adjacency lists."""
    u = dfs_data['ordering'][0]
    large_n = {}
    large_n[u] = 0
    stem = {}
    stem[u] = u
    b = {}
    b[u] = 0
    __branch_point_dfs_recursive(u, large_n, b, stem, dfs_data)
    dfs_data['N_u_lookup'] = large_n
    dfs_data['b_u_lookup'] = b
    return


def __branch_point_dfs_recursive(u, large_n, b, stem, dfs_data):
    """A recursive implementation of the BranchPtDFS function, as defined on page 14 of the paper."""
    v = dfs_data['adj'][u][0]
    large_w = wt(u, v, dfs_data)
    if large_w % 2 == 0:
        large_w += 1
    v_I = 0
    v_II = 0
    for v in [v for v in dfs_data['adj'][u] if wt(u, v, dfs_data) <= large_w]:
        if a(v, dfs_data) == u:
            large_n[v] = 0
            if wt(u, v, dfs_data) % 2 == 0:
                v_I = v
            else:
                b_u = b(u, dfs_data)
                l2_v = L2(v)
                if l2_v < b_u:
                    large_n[v] = 1
                elif b_u != 1:
                    x = stem[l2_v]
                    if large_n[x] != 0:
                        large_n[v] = large_n[x] + 1
                    elif dfs_data['graph'].adjacent(u, L1(v, dfs_data)):
                        large_n[v] = 2
                    else:
                        large_n[v] = large_n[u]
                if large_n[v] % 2 == 0:
                    v_II = v
                    break # Goto 1
    if v_II != 0:
        # Move v_II to head of Adj[u]
        dfs_data['adj'][u].remove(v_II)
        dfs_data['adj'][u].insert(0, v_II)
    elif v_I != 0:
        # Move v_I to head of Adj[u]
        dfs_data['adj'][u].remove(v_I)
        dfs_data['adj'][u].insert(0, v_I)
    first_time = True
    for v in dfs_data['adj'][u]:
        if a(v, dfs_data) == u:
            b[v] = u
            if first_time:
                b[v] = b[u]
            elif wt(u, v, dfs_data) % 2 == 0:
                large_n[v] = 0
            else:
                large_n[v] = 1
            stem[u] = v
            __branch_point_dfs_recursive(v, large_n, b, stem, dfs_data)
        first_time = False
    return


def __embed_branch(dfs_data):
    """Builds the combinatorial embedding of the graph. Returns whether the graph is planar."""
    u = dfs_data['ordering'][0]
    nonplanar = True
    dfs_data['LF'] = []
    dfs_data['RF'] = []
    dfs_data['FG'] = {}
    n = dfs_data['graph'].num_nodes()
    f0 = (0, n)
    g0 = (0, n)
    L0 = {'u': 0, 'v': n}
    R0 = {'x': 0, 'y': n}
    dfs_data['LF'].append(f0)
    dfs_data['RF'].append(g0)
    dfs_data['FG'][0] = [L0, R0]
    dfs_data['FG']['m'] = 0
    dfs_data['FG']['l'] = 0
    dfs_data['FG']['r'] = 0

    __embed_branch_recursive(u, nonplanar, dfs_data)

    return not nonplanar


def __embed_branch_recursive(u, nonplanar, dfs_data):
    """A recursive implementation of the EmbedBranch function, as defined on pages 8 and 22 of the paper."""
    for v in dfs_data['adj'][u]:
        nonplanar = True
        if a(v, dfs_data) == u:
            if b(v, dfs_data) == u:
                successful = __insert_branch(u, v, dfs_data)
                if not successful:
                    return
            __embed_branch_recursive(v, nonplanar, dfs_data)
            if nonplanar:
                return
        elif is_frond(u, v, dfs_data):
            successful = __embed_frond(u, v, dfs_data)
            if not successful:
                return
    nonplanar = False
    return


def __insert_branch(u, v, dfs_data):
    """Embeds a branch Bu(v) (as described on page 22 of the paper). Returns whether the embedding was successful."""
    w = L1(v, dfs_data)
    d_u = D(node_u, dfs_data)
    d_w = D(node_w, dfs_data)

    # Embed uw
    successful = __embed_frond(u, w, dfs_data)
    if not successful:
        return False

    # Embed a branch marker uu on the side opposite to uw, in the same frond block
    __embed_frond(u, u, dfs_data)

    # Determine which side uw was embedded on
    embedded_frond = (d_w, d_u)
    false_frond = (-d_w, d_u)
    embedded_marker = (d_u, d_u)
    false_marker = (-d_u, d_u)

    #print "Insert Branch:", false_frond, false_marker

    if dfs_data['LF'][-1] == embedded_frond:
        # It was embedded on the left side
        # Mark uw as a false frond
        #print "uw embedded left:", dfs_data['LF'][-1], dfs_data['RF'][-1]
        dfs_data['LF'][-1] = false_frond
        dfs_data['RF'][-1] = false_marker
    else:
        #print "uw embedded right:", dfs_data['LF'][-1], dfs_data['RF'][-1]
        dfs_data['RF'][-1] = false_frond
        dfs_data['LF'][-1] = false_marker

    return True


def __embed_frond(node_u, node_w, dfs_data):
    """Embeds a frond uw into either LF or RF. Returns whether the embedding was successful."""
    d_u = D(node_u, dfs_data)
    d_w = D(node_w, dfs_data)

    LF = dfs_data['LF']
    m = dfs_data['FG']['m']
    l_w = lw(dfs_data)
    r_w = rw(dfs_data)
    u_m = u(m, dfs_data)
    x_m = x(m, dfs_data)

    # There are multiple cases for both u and w
    # --Detect the case for u and store it for handling once the case for w is determined
    case_1 = False
    case_2 = False
    case_3 = False

    if d_u > u_m and d_u > x_m:
        case_1 = True
    elif d_u <= u_m and d_u > x_m:
        case_2 = True
    elif d_u > u_m and d_u <= x_m:
        case_3 = True
    else:
        # We should never get here, return false because there's no way we can embed this frond
        return False

    # --Detect the case for w and process the edge appropriately
    if d_w >= l_w and d_w >= r_w:
        # Case 4
        # --We do the same thing for all three u-cases: Add the frond to the left side
        LF.append( (d_w, d_u) )

        dfs_data['FG']['m'] += 1
        dfs_data['FG']['l'] += 1
        m = dfs_data['FG']['m']

        Lm = {'u': d_w, 'v': d_u}
        Rm = {'x': 0, 'y': n}
        dfs_data['FG'][m] = [Lm, Rm]
        return True
    elif d_w >= l_w and d_w < r_w:
        # Case 5
        return __do_case_5_work(d_w, d_u, case_1, case_2, case_3, dfs_data)
    elif d_w < l_w and d_w >= r_w:
        # Case 6
        return __do_case_6_work(d_w, d_u, case_1, case_2, case_3, dfs_data)
    elif d_w < l_w and d_w < r_w:
        # Case 7
        while d_w < l_w and d_w < r_w:
            if d_u > u_m and d_u > x_m:
                return False
            switch_sides(d_u, dfs_data)
            l_w = lw(dfs_data)
            r_w = rw(dfs_data)
            m = dfs_data['FG']['m']
            u_m = u(m, dfs_data)
            x_m = x(m, dfs_data)

        case_1 = False
        case_2 = False
        case_3 = False
        if d_u <= u_m and d_u > x_m:
            case_2 = True
        elif d_u > u_m and d_u <= x_m:
            case_3 = True

        if d_w >= l_w and d_w < r_w:
            # Case 5 redux
            return __do_case_5_work(d_w, d_u, case_1, case_2, case_3, dfs_data)
        if d_w < l_w and d_w >= r_w:
            # Case 6 redux
            return __do_case_6_work(d_w, d_u, case_1, case_2, case_3, dfs_data)
    else:
        # We should never get here, return false because there's no way we can embed this frond
        return False

    # We really shouldn't get to this point, but this is a catch-all just in case
    return False


def __do_case_5_work(d_w, d_u, case_1, case_2, case_3, dfs_data):
    """Encapsulates the work that will be done for case 5 of __embed_frond,
    since it gets used in more than one place."""
    # --We should only ever see u-cases 1 and 2
    if case_3:
        # --We should never get here
        return False

    # --Add the frond to the left side
    dfs_data['LF'].append( (d_w, d_u) )
    dfs_data['FG']['l'] += 1
    # --Add uw to Lm
    Lm = L(m, dfs_data)
    if d_w < Lm['u']:
        Lm['u'] = d_w
    if d_u > Lm['v']:
        Lm['v'] = d_u

    # --Case 2 requires a bit of extra work
    if case_2:
        Lm['u'] = d_w
        x_m1 = x(m-1, dfs_data)
        while d_w < x_m1:
            merge_Fm(dfs_data)
            m = dfs_data['FG']['m']
            x_m1 = x(m-1, dfs_data)

    return True


def __do_case_6_work(d_w, d_u, case_1, case_2, case_3, dfs_data):
    """Encapsulates the work that will be done for case 6 of __embed_frond,
    since it gets used in more than one place."""
    # --We should only ever see u-cases 1 and 3
    if case_2:
        # --We should never get here
        return False

    # --Add the frond to the right side
    dfs_data['RF'].append( (d_w, d_u) )
    dfs_data['FG']['r'] += 1
    # --Add uw to Rm
    Rm = R(m, dfs_data)
    if d_w < Rm['x']:
        Rm['x'] = d_w
    if d_u > Rm['y']:
        Rm['y'] = d_u

    # --Case 3 requires a bit of extra work
    if case_3:
        Rm['x'] = d_w
        u_m1 = u(m-1, dfs_data)
        while d_w < u_m1:
            merge_Fm(dfs_data)
            m = dfs_data['FG']['m']
            u_m1 = u(m-1, dfs_data)
    return True


def merge_Fm(dfs_data):
    """Merges Fm-1 and Fm, as defined on page 19 of the paper."""
    FG = dfs_data['FG']
    m = FG['m']
    FGm = FG[m]
    FGm1 = FG[m-1]

    if FGm[0]['u'] < FGm1[0]['u']:
        FGm1[0]['u'] = FGm[0]['u']

    if FGm[0]['v'] > FGm1[0]['v']:
        FGm1[0]['v'] = FGm[0]['v']

    if FGm[1]['x'] < FGm1[1]['x']:
        FGm1[1]['x'] = FGm[1]['x']

    if FGm[1]['y'] > FGm1[1]['y']:
        FGm1[1]['y'] = FGm[1]['y']

    del FG[m]
    FG['m'] -= 1


def switch_sides(d_u, dfs_data):
    """Switches Lm and Rm, as defined on page 20 of the paper."""
    m = dfs_data['FG']['m']
    u_m = u(m, dfs_data)

    if d_u <= u_m:
        l_w = lw(dfs_data)
        u_m1 = u(m-1, dfs_data)
        while u_m1 > l_w:
            merge_Fm(dfs_data)
            m = dfs_data['FG']['m']
            u_m1 = u(m-1, dfs_data)

        # l_w = r_w is handled dynamically by the switching of fronds below

        # l = r
        dfs_data['FG']['l'] = dfs_data['FG']['r']

        # adjust r so that gr is first frond preceding xm in RF
        x_m = x(m, dfs_data)
        r = len(dfs_data['RF']) - 1
        g_r = dfs_data['RF'][r][0]
        while g_r >= x_m:
            r -= 1
            g_r = dfs_data['RF'][r][0]
        dfs_data['FG']['r'] = r

        # changing r_w is also handled dynamically by the frond switching
    else:
        r_w = rw(dfs_data)
        x_m1 = x(m-1, dfs_data)
        while x_m1 > r_w:
            merge_Fm(dfs_data)
            m = dfs_data['FG']['m']
            x_m1 = x(m-1, dfs_data)

        # r_w = l_w is handled dynamically by the switching of fronds below

        # r = l
        dfs_data['FG']['r'] = dfs_data['FG']['l']

        # adjust l so that fl is first frond preceding um in LF
        u_m = u(m, dfs_data)
        l = len(dfs_data['LF']) - 1
        f_l = dfs_data['LF'][r][0]
        while f_l >= u_m:
            l -= 1
            f_l = dfs_data['LF'][l][0]
        dfs_data['FG']['l'] = l

        # changing l_w is also handled dynamically by the frond switching

    m = dfs_data['FG']['m']

    # Exchange the portion of the linked list LF between um and vm with the portion of RF between xm and ym
    LF = dfs_data['LF']
    RF = dfs_data['RF']

    u_m = u(m, dfs_data)
    v_m = v(m, dfs_data)
    x_m = x(m, dfs_data)
    y_m = y(m, dfs_data)

    # --These are the baseline indexes, they should be narrowed appropriately
    first_left_index = 1
    last_left_index = len(LF) - 1
    first_right_index = 1
    last_right_index = len(RF) - 1

    # --Narrow the left indexes
    while first_left_index < last_left_index:
        frond = LF[first_left_index]
        if u_m >= frond[0]:
            first_left_index -= 1
            break
        else:
            first_left_index += 1

    while first_left_index < last_left_index:
        frond = LF[last_left_index]
        if v_m < frond[1]:
            last_left_index -= 1
        else:
            last_left_index += 1
            break

    # --Narrow the right indexes
    while first_right_index < last_right_index:
        frond = RF[first_right_index]
        if x_m >= frond[0]:
            first_right_index -= 1
            break
        else:
            first_right_index += 1

    while first_right_index < last_right_index:
        frond = RF[last_right_index]
        if y_m < frond[1]:
            last_right_index -= 1
        else:
            last_right_index += 1
            break


    # --Grab the appropriate list slices from each list
    LF_slice = LF[first_left_index:last_left_index+1]
    RF_slice = RF[first_right_index:last_right_index+1]

    # --Remove the slices from each list
    del LF[first_left_index:last_left_index+1]
    del RF[first_right_index:last_right_index+1]

    # --Add the slice from the right list to the left list
    i = first_left_index
    for x in RF_slice:
        LF.insert(i, x)
        i += 1

    # --Add the slice from the left list to the right list
    i = first_right_index
    for x in LF_slice:
        RF.insert(i, x)
        i += 1

    # Descriptive Note: We can just switch the slices directly because we know that if there were any conflicts from
    # the switch, those fronds would also have been included in the switch.

    # Exchange um and xm , vm and ym , Lm and Rm
    # --Only Lm and Rm need to be exchanged, since um, xm, vm, and ym are all dynamically calculated
    old_rm = dfs_data['FG'][m][1]
    dfs_data['FG'][m][1] = dfs_data['FG'][m][0]
    dfs_data['FG'][m][0] = old_rm

    merge_Fm(dfs_data)


# Helper functions -- these are not directly specified by the overall algorithm, they just calculate intermediate data

def __get_dfs_data(graph, adj=None):
    """Internal function that calculates the depth-first search of the graph.
    Returns a dictionary with the following data:
        * 'ordering':        A dfs-ordering list of nodes
        * 'ordering_lookup': A lookup dict mapping nodes to dfs-ordering
        * 'node_lookup':     A lookup dict mapping dfs-ordering to nodes
        * 'edge_lookup':     A lookup dict mapping edges as tree-edges or back-edges
        * 'parent_lookup':   A lookup dict mapping nodes to their parent node
        * 'children_lookup': A lookup dict mapping nodes to their children
    """
    ordering, parent_lookup, children_lookup = depth_first_search_with_parent_data(graph, adjacency_lists=adj)
    ordering_lookup = dict(zip(ordering, range(1, len(ordering) + 1)))
    node_lookup = dict(zip(range(1, len(ordering) + 1), ordering))
    edge_lookup = {}

    for edge_id in graph.get_all_edge_ids():
        edge = graph.get_edge(edge_id)
        node_a, node_b = edge['vertices']
        parent_a = parent_lookup[node_a]
        parent_b = parent_lookup[node_b]
        if parent_a == node_b or parent_b == node_a:
            edge_lookup[edge_id] = 'tree-edge'
        else:
            edge_lookup[edge_id] = 'backedge'

    dfs_data = {}
    dfs_data['ordering'] = ordering
    dfs_data['ordering_lookup'] = ordering_lookup
    dfs_data['node_lookup'] = node_lookup
    dfs_data['edge_lookup'] = edge_lookup
    dfs_data['parent_lookup'] = parent_lookup
    dfs_data['children_lookup'] = children_lookup

    return dfs_data


def __calculate_adjacency_lists(graph):
    """Builds an adjacency list representation for the graph, since we can't guarantee that the
        internal representation of the graph is stored that way."""
    adj = {}
    for node in graph.get_all_node_ids():
        neighbors = graph.neighbors(node)
        adj[node] = neighbors
    return adj


def __get_all_lowpoints(dfs_data):
    """Calculates the lowpoints for each node in a graph."""
    lowpoint_1_lookup = {}
    lowpoint_2_lookup = {}

    ordering = dfs_data['ordering']

    for node in ordering:
        low_1, low_2 = __get_lowpoints(node, dfs_data)
        lowpoint_1_lookup[node] = low_1
        lowpoint_2_lookup[node] = low_2

    return lowpoint_1_lookup, lowpoint_2_lookup


def __get_lowpoints(node, dfs_data):
    """Calculates the lowpoints for a single node in a graph."""

    ordering_lookup = dfs_data['ordering_lookup']

    t_u = T(node, dfs_data)
    sorted_t_u = sorted(t_u, key=lambda a: ordering_lookup[a])
    lowpoint_1 = sorted_t_u[0]
    lowpoint_2 = sorted_t_u[1]

    return lowpoint_1, lowpoint_2


def __edge_weight(edge_id, dfs_data):
    """Calculates the edge weight used to sort edges."""
    graph = dfs_data['graph']
    edge_lookup = dfs_data['edge_lookup']

    edge = graph.get_edge(edge_id)
    u, v = edge['vertices']
    d_u = D(u, dfs_data)
    d_v = D(v, dfs_data)
    lp_1 = L1(v, dfs_data)
    d_lp_1 = D(lp_1, dfs_data)

    if edge_lookup[edge_id] == 'backedge' and d_v < d_u:
        return 2*d_v
    elif is_type_I_branch(u, v, dfs_data):
        return 2*d_lp_1
    elif is_type_II_branch(u, v, dfs_data):
        return 2*d_lp_1 + 1
    else:
        return 2*graph.num_nodes() + 1


def __calculate_bu_dfs(dfs_data):
    """Calculates the b(u) lookup table."""
    u = dfs_data['ordering'][0]
    b = {}
    b[u] = D(u, dfs_data)
    __calculate_bu_dfs_recursively(u, b, dfs_data)
    return b


def __calculate_bu_dfs_recursively(u, b, dfs_data):
    """Calculates the b(u) lookup table with a recursive DFS."""
    first_time = True
    for v in dfs_data['adj'][u]:
        if a(v, dfs_data) == u:
            if first_time:
                b[v] = b[u]
            else:
                b[v] = D(u, dfs_data)
            __calculate_bu_dfs_recursively(v, b, dfs_data)
        first_time = False


def is_type_I_branch(u, v, dfs_data):
    """Determines whether a branch uv is a type I branch."""
    if u != a(v, dfs_data):
        return False
    if u == L2(v, dfs_data):
        return True
    return False


def is_type_II_branch(u, v, dfs_data):
    """Determines whether a branch uv is a type II branch."""
    if u != a(v, dfs_data):
        return False
    if u < L2(v, dfs_data):
        return True
    return False


def is_leaf(v, dfs_data):
    """Determines if v is a leaf (has no descendants)."""
    return True if S(v, dfs_data) else False


def is_frond(u, v, dfs_data):
    """Determines if the edge uv is a frond ("backedge")."""
    d_u = D(u, dfs_data)
    d_v = D(v, dfs_data)
    edge_id = dfs_data['graph'].get_first_edge_id_by_node_ids(u, v)
    return True if dfs_data['edge_lookup'][edge_id] == 'backedge' and d_v < d_u else False


def __get_descendants(node, dfs_data):
    """Gets the descendants of a node."""
    list_of_descendants = []

    stack = deque()

    children_lookup = dfs_data['children_lookup']

    current_node = node
    children = children_lookup[current_node]
    dfs_current_node = D(current_node, dfs_data)
    for n in children:
        dfs_child = D(n, dfs_data)
        # Validate that the child node is actually a descendant and not an ancestor
        if dfs_child > dfs_current_node:
            stack.append(n)

    while len(stack) > 0:
        current_node = stack.pop()
        list_of_descendants.append(current_node)
        children = children_lookup[current_node]
        dfs_current_node = D(current_node, dfs_data)
        for n in children:
            dfs_child = D(n, dfs_data)
            # Validate that the child node is actually a descendant and not an ancestor
            if dfs_child > dfs_current_node:
                stack.append(n)

    return list_of_descendants


def __top_frond_left(dfs_data):
    """Returns the frond at the top of the LF stack."""
    return dfs_data['LF'][-1]


def __top_frond_right(dfs_data):
    """Returns the frond at the top of the RF stack."""
    return dfs_data['RF'][-1]


# Wrapper functions -- used to keep the syntax roughly the same as that used in the paper

def A(u, dfs_data):
    """The adjacency function."""
    return dfs_data['adj'][u]


def a(v, dfs_data):
    """The ancestor function."""
    return dfs_data['parent_lookup'][v]


def D(u, dfs_data):
    """The DFS-numbering function."""
    return dfs_data['ordering_lookup'][u]


def S(u, dfs_data):
    """The set of all descendants of u."""
    return __get_descendants(u, dfs_data)


def S_star(u, dfs_data):
    """The set of all descendants of u, with u added."""
    s_u = S(u, dfs_data)
    if u not in s_u:
        s_u.append(u)
    return s_u


def T(u, dfs_data):
    """T(u) consists of all vertices adjacent to u or any descendant of u."""
    return list(set([w for v in S_star(u, dfs_data) for w in A(v, dfs_data)]))


def B(u, v, dfs_data):
    """The branch at u containing v is the set of all edges incident on v or any descendant of v, if a(v) == u."""
    """Bu(v) = {wx | w is in S*(v)}"""
    if a(v, dfs_data) != u:
        return None

    return list(set([edge_id for w in S_star(v, dfs_data) for edge_id in dfs_data['graph'].get_node(w)['edges']]))


def stem(u, v, dfs_data):
    """The stem of Bu(v) is the edge uv in Bu(v)."""
    #return dfs_data['graph'].get_first_edge_id_by_node_ids(u, v)
    uv_edges = dfs_data['graph'].get_edge_ids_by_node_ids(u, v)
    buv_edges = B(u, v, dfs_data)
    for edge_id in uv_edges:
        if edge_id in buv_edges:
            return edge_id
    return None # We should never, ever get here


def L1(v, dfs_data):
    """The L1 lowpoint of the node."""
    return dfs_data['lowpoint_1_lookup'][v]


def L2(v, dfs_data):
    """The L2 lowpoint of the node."""
    return dfs_data['lowpoint_2_lookup'][v]


def wt(u, v, dfs_data):
    """The wt_u[v] function used in the paper."""
    # Determine the edge_id
    edge_id = dfs_data['graph'].get_first_edge_id_by_node_ids(u, v)
    # Pull the weight of that edge
    return dfs_data['edge_weights'][edge_id]


def _L(dfs_data):
    """L(T) contains leaves and branch points for the DFS-tree T."""
    """L(T) = {v | the first w in Adj[v] corresponds to a frond vw}."""
    node_set = set()
    for v, adj in dfs_data['adj'].items():
        w = adj[0]
        if is_frond(v, w, dfs_data):
            node_set.add(v)
    return list(node_set)


def b(u, dfs_data):
    """The b(u) function used in the paper."""
    return dfs_data['b_u_lookup'][u]


def N(u, dfs_data):
    """The N(u) function used in the paper."""
    return dfs_data['N_u_lookup'][u]


def N_prime(u, dfs_data):
    """The N'(u) function used in the paper."""
    return dfs_data['N_prime_u_lookup'][u]


def F(i, dfs_data):
    """The block of fronds in the frond graph."""
    return dfs_data['FG'][i]


def L(i, dfs_data):
    """The set of fronds on the left side of the frond graph."""
    return F(i, dfs_data)[0]


def R(i, dfs_data):
    """The set of fronds on the right side of the frond graph."""
    return F(i, dfs_data)[1]


def u(i, dfs_data):
    """The minimum vertex (DFS-number) in a frond contained in Li."""
    return L(i, dfs_data)['u']


def v(i, dfs_data):
    """The maximum vertex (DFS-number) in a frond contained in Li."""
    return L(i, dfs_data)['v']


def x(i, dfs_data):
    """The minimum vertex (DFS-number) in a frond contained in Ri."""
    return R(i, dfs_data)['x']


def y(i, dfs_data):
    """The maximum vertex (DFS-number) in a frond contained in Ri."""
    return R(i, dfs_data)['y']


def lw(dfs_data):
    """The minimum frond endpoint that can be embedded on the left side of the current frond block."""
    l = dfs_data['FG']['l']
    return dfs_data['LF'][l][0]


def rw(dfs_data):
    """The minimum frond endpoint that can be embedded on the right side of the current frond block."""
    r = dfs_data['FG']['r']
    return dfs_data['RF'][r][0]