"""Data structures for handling various forms of multilayer networks.
"""

import math,itertools

COLON=slice(None,None,None)


class MultilayerNetwork(object):
    """General multilayer network with a tensor-like interface.

    See Reference [1] for background on the definition of this class.

    There are several ways of accessing the edges and nodes of the network. If there 
    is a single aspect, then the following notation can be used:

    >>> net[i,s]                   #node i at layer s
    >>> net[i,j,s,r]               #edge between nodes i and j and layers s and r
    >>> net[i,j,s] == net[i,j,s,s] #edge between nodes i and j at layer s

    Following slicing notation can also be used:

    >>> net[i,:,s,:] == net[i,s]   #node i at layer s
    >>> net[i,j,s,:]               #node i at layer s, but only links to j are visible
    >>> net[i,:,s,r]               #node i at layer s, but only links to layer r are visible
    >>> net[i,:,s] == net[i,:,s,s] 

    Similar notation holds for two (or more) aspects:

    >>> net[i,s,x]                 #node i at layer s in aspect 1 and at layer x in aspect 2
    >>> net[i,j,s,x]               #link i,j at layer s in aspect 1 and layer x in aspect 2 = i,j,s,s,x,x
    >>> net[i,j,s,r,x,y]           #link i,j between layers s and r in aspect 1 and between layers x and y in aspect 2
    >>> net[i,:,s,:,x,:] == net[i,s,x]
    >>> net[i,j,s,:,x,y]           #node i at layer s and y, but only links to j and y are visible
    >>> net[i,:,s,x] == net[i,:,s,s,x,x]


    Parameters
    ----------
    aspects : int
       Number of aspects
    noEdge : object
       Any object signifying that there is no edge.
    directed : bool
       True if the network is directed, otherwise it's
       undirected.
    fullyInterconnected : bool
       Determines if the network is fully interconnected, i.e. all nodes
       are shared between all layers.

    Notes
    -----
    The default data structure behind this class is a graph similar to the 
    one described in Reference [1] implemented with nested dictionaries. 
    The downside to this implementation is that, for example, iterating through
    all the inter-layer links is not possible without inspecting also the
    inter-layer links.

    References
    ----------
    [1] Multilayer Networks. Mikko Kivela, Alexandre Arenas, Marc Barthelemy, 
    James P. Gleeson, Yamir Moreno, Mason A. Porter, arXiv:1309.7233 [physics.soc-ph]

    See also
    --------
    MultiplexNetwork : A class for multiplex networks

    """
    def __init__(self,
                 aspects=0,
                 noEdge=0,
                 directed=False,
                 fullyInterconnected=True):
        assert aspects>=0

        self.aspects=aspects
        self.directed=directed
        self.noEdge=noEdge
        self._init_slices(aspects)
        
        self._net={}

        #should keep table of degs and strenghts

    def _init_slices(self,aspects):
        self.slices=[] #set for each dimension
        for a in range(aspects+1):
            self.slices.append(set())
       
        
    #@classmehtod
    def _link_to_nodes(self,link):
        """Returns the link as tuple of nodes in the graph representing
        the multislice structure. I.e. when given (i,j,s_1,r_1, ... ,s_d,r_d)
        (i,s_1,...,s_d),(j,r_1,...,r_d) is returned.
        """
        return (link[0],)+link[2::2],(link[1],)+link[3::2]
    #@classmehtod
    def _nodes_to_link(self,node1,node2):
        """Returns a link when tuple of nodes is given in the graph representing
        the multislice structure. I.e. when given (i,s_1,...,s_d),(j,r_1,...,r_d) 
        (i,j,s_1,r_1, ... ,s_d,r_d) is returned.
        """
        assert len(node1)==len(node2)
        l=[]
        for i,n1 in enumerate(node1):
            l.append(n1)
            l.append(node2[i])
        return tuple(l)
    #@classmehtod
    def _short_link_to_link(self,slink):
        """ Returns a full link for the shortened version of the link. That is,
        if (i,j,s_1,...,s_d) is given as input, then (i,j,s_1,s_1,...,s_d,s_d) is 
        returned.
        """
        l=list(slink[:2])
        for k in slink[2:]:
            l.append(k)
            l.append(k)

        return tuple(l)
    
    def __len__(self):
        return len(self.slices[0])

    def add_node(self,node,aspect):
        """Adds an empty node to the aspect.
        Does nothing if node already exists.
        """
        self.slices[aspect].add(node)

    def _get_link(self,link):
        """Return link weight or 0 if no link.
        
        This is a private method, so no sanity checks on the parameters are
        done at this point.

        Parameters
        ---------
        link(tuple) : (i,j,s_1,r_1, ... ,s_d,r_d)
        """
        node1,node2=self._link_to_nodes(link)
        if node1 in self._net:
            if node2 in self._net[node1]:
                return self._net[node1][node2]
        return self.noEdge

    def _set_link(self,link,value):
        #keep track of nodes and layers in net?
        #remove nodes if they become empty?
        node1,node2=self._link_to_nodes(link)
        if value==self.noEdge:
            if node1 in self._net:
                if node2 in self._net[node1]:
                    del self._net[node1][node2]
                    if not self.directed:
                        del self._net[node2][node1]
        else:
            if not node1 in self._net:
                self._net[node1]={}
            if not node2 in self._net:
                self._net[node2]={}
            
            self._net[node1][node2]=value
            if not self.directed:
                self._net[node2][node1]=value

    def _get_degree(self,node, dims=None):
        """Private method returning nodes degree (number of neighbors).

        See _iter_neighbors for description of the parameters.
        """
        #TODO: lookuptables for intradimensional degrees

        if dims==None:
            if node in self._net:
                return len(self._net[node])
            else:
                return 0
        else:
            return len(list(self._iter_neighbors(node,dims)))

    def _get_strength(self,node, dims=None):
        """Private method returning nodes strenght (sum of weights).

        See _iter_neighbors for description of the parameters.
        """
        #TODO: lookuptables for intradimensional strengths        
        return sum(map(lambda n:self._get_link(self._nodes_to_link(node,n)),self._iter_neighbors(node,dims)))


    def _iter_neighbors(self,node,dims):
        """Private method to iterate over neighbors of a node.

        Parameters
        ----------
        node(tuple) : (i,s_1,...,s_d)
        dims : If None, iterate over all neighbors. If tuple of size d+1,
               then we iterate over neighbors which are have exactly the same
               value at each dimension in the tuple or None. E.g. when
               given ('a',None,'x'), iterate over all neighbors which are node
               'a' and in slice 'x' in the second dimension.

        """
        if node in self._net:
            if dims==None:
                for neigh in self._net[node]:
                    yield neigh
            else:
                for neigh in self._net[node]:
                    if all(map(lambda i:dims[i]==None or neigh[i]==dims[i], range(len(dims)))):
                        yield neigh

    def __getitem__(self,item):
        """
        aspects=1
        i,s     = node i at layer s
        i,j,s   = link i,j at layer s = i,j,s,s
        i,j,s,r = link i,j between layers s and r

        i,:,s,: = i,s = node i at layer s
        i,j,s,: = node i at layer s, but only links to j are visible
        i,:,s,r = node i at layer s, but only links to layer r are visible

        i,:,s   = i,:,s,s
        Not implemented yet:
        i,s,:   = i,i,s,:

        aspects=2
        i,s,x       = node i at layer s in aspect 1 and at layer x in aspect 2
        i,j,s,x     = link i,j at layer s in aspect 1 and layer x in aspect 2 = i,j,s,s,x,x
        i,j,s,r,x,y = link i,j between layers s and r in aspect 1 and between layers x and y in aspect 2

        i,:,s,:,x,: = i,s,x
        i,j,s,:,x,y = node i at layer s and y, but only links to j and y are visible
        ...

        i,:,s,x = i,:,s,s,x,x
        Not implemented yet:
        i,s,:,x = i,i,s,:,x,x
        i,s,x,: = i,i,s,s,x,:

        i,:,s,:,x = i,:,s,:,x,x
        i,s,:,x,: = i,i,s,:,x,:
        

        """        
        d=self.aspects+1
        if not isinstance(item,tuple):
            item=(item,)
        if len(item)==d: #node
            return MultilayerNode(item,self)
        elif len(item)==2*d: #link, or a node if slicing
            colons=0
            layers=[]
            for i in range(d):
                if item[2*i+1]!=COLON:
                    layers.append(item[2*i])
                else:
                    colons+=1
                    layers.append(None)
            if colons>0:
                return MultilayerNode(self._link_to_nodes(item)[0],self,layers=layers)
            else:
                return self._get_link(item)
        elif len(item)==d+1: #interslice link or node if slicing            
            if COLON not in item[2:]: #check if colons are in the slice indices
                return self[self._short_link_to_link(item)]
            else:
                raise NotImplemented("yet.")
        else:
            if d>1:
                raise KeyError("%d, %d, or %d indices please."%(d,d+1,2*d))
            else: #d==1
                raise KeyError("1 or 2 indices please.")

    def __setitem__(self,item,val):
        d=self.aspects+1

        if not isinstance(item,tuple):
            item=(item,)
        if len(item)==2*d:
            link=item
            #self._set_link(item,val)
        elif len(item)==d+1:
            link=self._short_link_to_link(item)
        else:
            raise KeyError("Invalid number of indices.")

        #There might be new nodes, add them to sets of nodes
        for i in range(2*d):
            self.add_node(link[i],int(math.floor(i/2))) #just d/2 would work, but ugly

        self._set_link(link,val)



    def iter_dimension(self,aspect):
        for node in self.slices[aspect]:
            yield node

    def __iter__(self):
        """Iterates over all nodes.
        """
        for node in self.slices[0]:
            yield node

    @property
    def edges(self):
        if self.directed:
            for node in itertools.product(*self.slices):
                for neigh in self[node]:                
                    if self.aspects==0:
                        neigh=(neigh,)
                    link=self._nodes_to_link(node,neigh)
                    yield link+(self[link],)
        else:
            iterated=set()
            for node in itertools.product(*self.slices):
                for neigh in self[node]:                
                    if self.aspects==0:
                        neigh=(neigh,)
                    if neigh not in iterated:
                        link=self._nodes_to_link(node,neigh)
                        yield link+(self[link],)            
                iterated.add(node)

    def write_flattened(self,output):
        nodes=map(lambda x: tuple(reversed(x)),sorted(itertools.product(*map(lambda i:sorted(self.slices[i]),reversed(range(len(self.slices)))))))
        for i in nodes:
            row=[str(self[i][j]) for j in nodes]
            output.write(" ".join(row)+"\n")
        output.close()


    def get_supra_adjacency_matrix(self,includeCouplings=True):
        import numpy
        if self.aspects>0:
            nodes=map(lambda x: tuple(reversed(x)),sorted(itertools.product(*map(lambda i:sorted(self.slices[i]),reversed(range(len(self.slices)))))))
            matrix=numpy.zeros((len(nodes),len(nodes)),dtype=float)
            for i_index,i in enumerate(nodes):
                for j_index,j in enumerate(nodes):
                    if includeCouplings or i[1:]==j[1:]:
                        matrix[i_index,j_index]=self[i][j]
        else:
            nodes=sorted(self)
            matrix=numpy.zeros((len(nodes),len(nodes)),dtype=float)
            for i_index,i in enumerate(nodes):
                for j_index,j in enumerate(nodes):
                    if i_index!=j_index:
                        matrix[i_index,j_index]=self[i][j]

        return numpy.matrix(matrix),nodes

class MultilayerNode(object):
    def __init__(self,node,mnet,layers=None):
        """A node in multilayer network. 
        """
        self.node=node
        self.mnet=mnet
        self.layers=layers

    def __getitem__(self,item):
        """
        example:
        net[1,'a','x'][:,:,'y']=net[1,:,'a',:,'x','y']
        """
        if self.mnet.aspects==0:
            item=(item,)
        return self.mnet[self.mnet._nodes_to_link(self.node,item)]

    def __setitem__(self,item,value):
        if self.mnet.aspects==0:
            item=(item,)
        self.mnet[self.mnet._nodes_to_link(self.node,item)]=value

    def deg(self,*layers):
        assert len(layers)==0 or len(layers)==(self.mnet.aspects+1)
        if layers==():
            layers=self.layers
        return self.mnet._get_degree(self.node,layers)
    def str(self,*layers):
        assert len(layers)==0 or len(layers)==(self.mnet.aspects+1)
        if layers==():
            layers=self.layers
        return self.mnet._get_strength(self.node,layers)
    def __iter__(self):
        if self.mnet.aspects>0:
            for node in self.mnet._iter_neighbors(self.node,self.layers):
                yield node #maybe should only return the indices that can change?
        else:
            for node in self.mnet._iter_neighbors(self.node,self.layers):
                yield node[0]
    def layers(self,*layers):
        return MultilayerNode(self.node,self.mnet,layers=layers)

class MultilayerNetworkWithParent(MultilayerNetwork):
    def _set_parent(self,parent):
        self.parent=parent
    def _set_name(self,name):
        self._name=name
    def add_node(self,node,aspect):
        self.parent.add_node(node,0)
        MultilayerNetwork.add_node(self,node,aspect)
        if not self.parent.fullyInterconnected:
            if node not in self.parent._nodeToLayers:
                 self.parent._nodeToLayers[node]=set()
            self.parent._nodeToLayers[node].add(self._name)

class MultiplexNetwork(MultilayerNetwork):
    """Multiplex network as a special case of multilayer network.

    Parameters
    ----------
    couplings : list
       A list with lenght equal to number of aspects. Each coupling must be 
       either a policy or a network. Policy is a tuple: (type, weight)
       Policy types: 'ordinal', 'categorical'.
    noEdge : object
       Any object signifying that there is no edge.
    directed : bool
       True if the network is directed, otherwise it's
       undirected.
    fullyInterconnected : bool
       Determines if the network is fully interconnected, i.e. all nodes
       are shared between all layers.
    
    Notes
    -----
    The default implementation for this type of networks is 'sequence of
    graphs'. That is, each intra-layer network is stored separately and 
    accessing and modifying the intra-layer networks is independent of the
    other intra-layer networks. The couplings edges are not stored explicitely
    but they are only generated when needed.

    See also
    --------
    MultilayerNetwork : A class for more general type of multilayer networks

    """

    def __init__(self,couplings=None,directed=False,noEdge=0,fullyInterconnected=True):
        self.directed=directed
        self.noEdge=noEdge

        self.fullyInterconnected=fullyInterconnected
        if not fullyInterconnected:
            self._nodeToLayers={}

        if couplings!=None:
            #assert len(couplings)==dimensions
            self.couplings=[]
            for coupling in couplings:
                if isinstance(coupling,tuple):
                    self.couplings.append(coupling)
                elif isinstance(coupling,MultilayerNetwork):
                    self.couplings.append((coupling,))
                else:
                    raise ValueError("Invalid coupling type: "+str(type(coupling)))
            self.aspects=len(couplings)
        else:
            #couplings=map(lambda x:None,range(dimensions))
            self.aspects=0

        self._init_slices(self.aspects)
        
        #diagonal elements, map with keys as tuples of slices and vals as MultiSliceNetwork objects
        #keys are not tuples if dimensions==2
        self.A={} 

    def _get_edge_inter_aspects(self,link):
        r"""Returns list of aspects where the two nodes of $G_M$ differ.
        """
        dims=[]
        for d in range(self.aspects+1):
            if link[2*d]!=link[2*d+1]:
                dims.append(d)
        return dims

    def _get_A_with_tuple(self,layer):
        """Return self.A. Layer must be given as tuple.
        """
        if self.aspects==1:
            return self.A[layer[0]]
        else:
            return self.A[layer]

    def _add_A(self,node):
        net=MultilayerNetworkWithParent(aspects=0)
        net._set_parent(self)
        if not self.fullyInterconnected:
            if self.aspects==1:
                net._set_name((node,))
            else:
                net._set_name(node)
        self.A[node]=net

    def add_node(self,node,aspect):
        """ Adds node or a layer to given dimension.

        Maybe we should have add_node and add_layer methods separately?

        Examples
        --------
        >>> myNet.add_node('myNode',0) #Adds a new node with label 'myNode'
        >>> myNet.add_node('myLayer',1) #Adds a new layer to the first dimension
        """
        #overrrides the parent method

        #check if new diagonal matrices needs to be added
        if node not in self.slices[aspect]:
            if aspect>0:            
                if self.aspects>1:
                    new_slices=list(self.slices[1:])
                    new_slices[aspect-1]=[node]
                    for s in itertools.product(*new_slices):
                        self._add_A(s)
                else:
                    self._add_A(node)

            #call parent method
            MultilayerNetwork.add_node(self,node,aspect)


    def _has_layer_with_tuple(self,layer):
        """Return true if layer in self.A. Layer must be given as tuple.
        """
        if self.aspects==1:
            return layer[0] in self.A
        else:
            return layer in self.A


    def _get_link(self,link):
        """Overrides parents method.
        """
        d=self._get_edge_inter_aspects(link)
        if len(d)==1: #not a self-link, or link with multiple different cross-aspects
            if d[0]>0:
                assert link[0]==link[1]
                if not link[0] in self.slices[0]:
                    return self.noEdge
                if not self.fullyInterconnected:
                    supernode1, supernode2=self._link_to_nodes(link)
                    if not (link[0] in self._get_A_with_tuple(supernode1[1:]).slices[0] and link[0] in self._get_A_with_tuple(supernode2[1:]).slices[0]):
                        return self.noEdge
                coupling=self.couplings[d[0]-1]                
                if coupling[0]=="categorical":
                        return coupling[1] 
                elif coupling[0]=="ordinal":
                    if link[2*d[0]]+1==link[2*d[0]+1] or link[2*d[0]]==link[2*d[0]+1]+1:
                        return coupling[1]
                    else:
                        return self.noEdge
                elif isinstance(coupling[0],MultilayerNetwork):
                    return self.couplings[d[0]-1][0][link[2*d[0]],link[2*d[0]+1]]
                else:
                    raise Exception("Coupling not implemented: "+str(coupling))
            else:
                if self._has_layer_with_tuple(link[2::2]):
                    return self._get_A_with_tuple(link[2::2])[link[0],link[1]]
                else:
                    return self.noEdge
        else:
            return self.noEdge
                
    def _set_link(self,link,value):
        """Overrides parents method.
        """
        d=self._get_edge_inter_aspects(link)
        if len(d)==1 and d[0]==0:
            S=link[2::2]
            self._get_A_with_tuple(S)[link[0],link[1]]=value
        elif len(d)==0:
            raise KeyError("No self-links.")
        else:
            raise KeyError("Can only set links in the node dimension.")


    def _get_dim_degree(self,supernode,aspect):
        coupling_type=self.couplings[aspect-1][0]
        if coupling_type=="categorical":
            if self.fullyInterconnected:
                return len(self.slices[aspect])-1
            else:
                if supernode[1:] in self._nodeToLayers[supernode[0]]:
                    if self.aspects==1:
                        return len(self._nodeToLayers[supernode[0]])-1
                    else:
                        return len(filter(lambda x:x[aspect]==supernode[aspect],self._nodeToLayers[supernode[0]])) -1
                else:
                    return 0
        elif coupling_type=="ordinal":
            up,down=supernode[aspect]+1,supernode[aspect]-1
            if self.fullyInterconnected:
                return int(up in self.slices[aspect])+int(down in self.slices[aspect])
            else:
                return int(supernode[:aspect]+(up,)+supernode[aspect+1:] in self._nodeToLayers[supernode[0]])+int(supernode[:aspect]+(down,)+supernode[aspect+1:] in self._nodeToLayers[supernode[0]])
        elif isinstance(coupling_type,MultilayerNetwork):
            return self.couplings[aspect-1][0][supernode[aspect]].deg()
        else:
            raise NotImplemented()

    def _get_dim_strength(self,node,aspect):
        coupling_str=self.couplings[aspect-1][1]
        coupling_type=self.couplings[aspect-1][0]
        if isinstance(coupling_type,MultilayerNetwork):
            raise Exception() #please implement this
        return self._get_dim_degree(node,aspect)*coupling_str


    def _iter_dim(self,supernode,aspect):
        coupling_type=self.couplings[aspect-1][0]
        if coupling_type=="categorical":            
            if self.fullyInterconnected:
                for n in self.slices[aspect]:
                    if n!=supernode[aspect]:                    
                        yield supernode[:aspect]+(n,)+supernode[aspect+1:]
            elif supernode[0] in self._get_A_with_tuple(supernode[1:]).slices[0]:
                for layers in self._nodeToLayers[supernode[0]]:
                    if layers!=supernode[1:]:                    
                        yield (supernode[0],)+layers
        elif coupling_type=="ordinal":
            up,down=supernode[aspect]+1,supernode[aspect]-1
            if self.fullyInterconnected:
                if up in self.slices[aspect]:
                    yield supernode[:aspect]+(up,)+supernode[aspect+1:]
                if down in self.slices[aspect]:
                    yield supernode[:aspect]+(down,)+supernode[aspect+1:]
            else:
                if supernode[1:aspect]+(up,)+supernode[aspect+1:] in self._nodeToLayers[supernode[0]]:
                    yield supernode[:aspect]+(up,)+supernode[aspect+1:]
                if supernode[1:aspect]+(down,)+supernode[aspect+1:] in self._nodeToLayers[supernode[0]]:
                    yield supernode[:aspect]+(down,)+supernode[aspect+1:]
        else:
            raise NotImplemented()
        
    def _select_dimensions(self,node,dims):
        if dims==None:
            for d in range(self.aspects+1):
                yield d
        else:
            l=[]
            for d,val in enumerate(dims):
                if val!=None and node[d]!=val:
                    return
                if val==None:
                    l.append(d)
            for d in l:
                yield d

    def _get_degree(self,node, dims):
        """Overrides parents method.
        """
        k=0
        for d in self._select_dimensions(node,dims):
            if d==0:
                k+=self._get_A_with_tuple(node[1:])[node[0]].deg()
            else:
                k+=self._get_dim_degree(node,d)
        return k

    def _get_strength(self,node, dims):
        """Overrides parents method.
        """
        s=0
        for d in self._select_dimensions(node,dims):
            if d==0:
                s+=self._get_A_with_tuple(node[1:])[node[0]].str()
            else:
                s+=self._get_dim_strength(node,d)
        return s

    def _iter_neighbors(self,node,dims):
        """Overrides parents method.
        """
        for d in self._select_dimensions(node,dims):
            if d==0:                
                for n in self._get_A_with_tuple(node[1:])[node[0]]:
                    yield (n,)+node[1:]
            else:
                for n in self._iter_dim(node,d):
                    yield n


    def get_couplings(self,aspect):
        """Returns a view to a network of couplings between nodes and
        their counterparts in other slices of the given dimension.        
        """
        pass

    def set_connection_policy(self,aspect,policy):
        pass

class FlatMultilayerNetworkView(MultilayerNetwork):
    """

    fnet[(1,'a','b')]
    fnet[(1,'a','b'),(2,'a','b')]

    """
    def __init__(self,mnet):
        self.mnet=mnet
        self.aspects=0

    def _flat_node_to_node(self,node):
        pass

    def _flat_edge_to_edge(self,edge):
        pass


    def _get_link(self,link):
        """Overrides parents method.
        """
        return self.mnet[tuple(itertools.chain(*zip(*a)))]
                
    def _set_link(self,link,value):
        """Overrides parents method.
        """
        raise NotImplemented("yet.")

    def _get_degree(self,node, dims):
        """Overrides parents method.
        """
        raise NotImplemented("yet.")

    def _iter_neighbors(self,node,dims):
        """Overrides parents method.
        """
        raise NotImplemented("yet.")

class ModularityMultilayerNetworkView(MultilayerNetwork):
    def __init__(self,mnet,gamma=1.0):
        self.gamma=gamma
        self.mnet=mnet

        self.slices=mnet.slices
        self.aspects=mnet.aspects

        #precalc ms,u
        self.m={}
        for s in itertools.product(*mnet.slices[1:]):
            for node in mnet:
                self.m[s]=self.m.get(s,0)+mnet[(node,)+s][(COLON,)+s].str()
            self.m[s]=self.m[s]/2.0
        self.u=0
        for i in itertools.product(*mnet.slices):
            for j in itertools.product(*mnet.slices):
                self.u+=mnet[i][j]
        self.oneper2u=1.0/self.u/2.0

    def _get_link(self,item):
        v=self.mnet[item]

        if item[2::2]==item[3::2]: #its inside slice
            s=item[2::2]
            kis=self.mnet[(item[0],)+s][(COLON,)+s].str()
            kjs=self.mnet[(item[1],)+s][(COLON,)+s].str()
            ms=self.m[s]
            return v-self.gamma*kis*kjs/float(2.0*ms)
        else:
            return v


try:
    import networkx
    class FlattenedMultilayerNetworkxView(networkx.Graph):
        pass
except ImportError:
    pass



if __name__ == '__main__':
    import tests.net_test
    tests.net_test.test_net()