"""cs1graphics.py

Copyright 2008-2012, David Letscher and Michael H. Goldwasser

Go to www.cs1graphics.org for more information.

This is Version 1.2a2 alpha bugfix release (18 January 2012)
       Detabified (15 April 2012)
"""

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Configuration Options
_nativeThreading = False     # if True, this allows for true multi-threading
_mathMode = False            # if True, coordinate system uses lower-left origin
_RECURSIVE_LIMIT = 10
_debug = 0
_dashMultiplier = 2          # oddity about whether pattern should be (a,b) or (a,b,a,b)

import copy as _copy
import math as _math
import random as _random
import time as _time
import threading as _threading
import atexit as _atexit
import tempfile as _tempfile
import os as _os
import sys as _sys
import traceback as _traceback
from array import array as _array
import cStringIO as _cStringIO
import base64 as _base64

# change in module names for Python 2 vs 3
try:
    import Queue as _Queue
except ImportError:
    import queue as _Queue     # Python 3


try:    
    import thread as _thread
except ImportError:
    import _thread as _thread  # Python 3

try:    
    import Tkinter as _Tkinter
except ImportError:
    try:
        import tkinter as _Tkinter # Python 3
    except ImportError:
        raise ImportError('cs1graphics requires that Tkinter be installed')

try:
    import Image as _Image
    import ImageDraw as _ImageDraw
    import ImageTk as _ImageTk
except ImportError:
    raise ImportError('cs1graphics requires that PIL be installed')
_pilAvailable = True

# Library
_tkroot = None

_ourRandom = _random.Random()
_ourRandom.seed(1234)     # initialize the random seed so that behaviors are reproducible

# support for Python 2.x/3.x.
# We want to use isinstance(foo, basestring) in either case
try:
    unicode
except NameError:
    basestring = unicode = str


# Global Configuration Controls
def configureNativeThreading():
    """Configures cs1graphics to run in native multi-threaded mode.

    By default, the library is predominantly single-threaded, with all
    rendering in the primary thread and EventHandlers activated only
    when the end of the main thread is reached, or an explicit
    (blocking) call to startEventHandling() is made.

    On systems that support accessing Tkinter from a secondary thread,
    an initial call to this function switches to a multi-threaded
    model in which case all rendering is managed by a secondary
    thread, and EventHandlers are immediately activated once
    registered without blocking the primary thread.

    Note: This command must be executed prior to the use of any core
    library functionality.

    Note: As an alternative, your cs1graphics installation can be
    configured to use native threading as the default mode by setting
    the variable, _nativeThread = True, in the file cs1graphics.py.
    """
    if _graphicsManager._state != 'Initial':
        raise GraphicsError('configuration must occur prior to other use of the library')
    global _nativeThreading
    _nativeThreading = True

def configureMathMode():
    """Forces cs1graphics to use standard math coordinate system.

    By default, cs1graphics uses a standard computer graphics
    coordinate system with the origin at the top-left and the positive
    y-axis oriented downward.

    If this function is invoked, it causes canvases to use a standard
    mathematics coordinate system with the origin at bottom-left and
    the positive y-axis oriented upward.  In math mode, a positive
    rotation is conventionally counterclockwise rather than clockwise.

    NOTE: This command must be executed prior to the use of any core
    library functionality.

    Note: As an alternative, your cs1graphics installation can be
    configured to use the math coordinate system by default by setting
    the variable, _mathMode = True, in the file cs1graphics.py.
    """
    if _graphicsManager._state != 'Initial':
        raise GraphicsError('configuration must occur prior to other use of the library')
    global _mathMode
    _mathMode = True

def configureSetRecursionLimit(limit):
    """Changes the limit on recursion for drawable inclusion.

    In cases such as when adding a layer to itself, the drawing
    process is intentionally capped with some maximum recursive depth
    to avoid an infinite recursion.  By default, that limit is 10.
    This function allows that to be changed.
    """
    if _graphicsManager._state != 'Initial':
        raise GraphicsError('configuration must occur prior to other use of the library')
    if not isinstance(limit, int):
        raise TypeError('limit should be an integer')
    if limit < 1:
        raise ValueError('limit must be positive')
    global _RECURSIVE_LIMIT
    _RECURSIVE_LIMIT = limit

    
class GraphicsError(Exception):
    def __init__(self, message, recoverable=False):
        Exception.__init__(self, message)
        self._recoverable = recoverable


# Data structures
class _OrderedMap:

  """Implements an ordered map.

  Although we do not formally require the keys to be hashable, the
  expectation is that they should not be mutated.

  By default, ordering is based on < operator, but the user
  can provide a non-standard boolean function for comparing keys.
  
  This implementation is based upon an underlying treap.

  """

  def _less(a, b):
    """Generic version of comparison function."""
    return a < b
  _less = staticmethod(_less)

  def __init__(self, less=None):
    """Create an empty map.

    less is a boolean function with callingsignature less(keyA, keyB)
    that returns True if keyA is strictly less than keyB.

    If not sent, the default < operator is used.

    """
    self._root = None
    self._size = 0
    if less is not None:
      self._less = less

  def __len__(self):
    """Return the size of the map."""
    return self._size

  def _trace(self, key):
    """Walk path looking for given key.

    Return the node that has the key, if any.
    Otherwise return the last true node visited.
    In case of an empty map, None is returned.

    """
    if len(self) > 0:
      walk = self._root
      while walk is not None and \
            (self._less(key, walk.key) or self._less(walk.key, key)):
        # no match thus far
        trail = walk
        if self._less(key, walk.key):
          walk = walk.left
        else:
          walk = walk.right
      if walk is not None:
        result =  walk
      else:
        result =  trail
    else:
      result = None

    return result

  def __delitem__(self, key):
    """Remove the entry assoicated with the key.

    KeyError results if key does not exist.

    """
    temp = self.find(key)
    if temp is None:
      raise KeyError(repr(key))
    self.remove(temp)

  def __getitem__(self, key):
    """Return the value associated with the key.

    KeyError results if key does not exist.
    """
    temp = self.find(key)
    if temp is None:
      raise KeyError(repr(key))
    else:
      return temp.value()

  def __setitem__(self, key, value):
    """Associate key to value.

    If key exists, old value is overwritten with new.
    If key does not exist, it is added to the map.

    """
    self.insert(key, value)   # ignore return value

  def find(self, key):
    """Return an iterator to the key's position, if found.

    None is returned if key not found.

    """
    walk = self._trace(key)
    if walk is not None and not \
       (self._less(key, walk.key) or self._less(walk.key, key)):
      return _OrderedMap.iterator(walk)
    else:
      return None

  def __contains__(self, key):
    """Return True if key in the map."""
    return self.find(key) is not None

  def first(self):
    """Return iterator to the first element of the map.
    
    None is returned if map is empty.

    """
    if len(self) > 0:
      return _OrderedMap.iterator(self._root.subtreeMin())
    else:
      return None

  def last(self):
    """Return iterator to the last element of the map.
    
    None is returned if map is empty.

    """
    if len(self) > 0:
      return _OrderedMap.iterator(self._root.subtreeMax())
    else:
      return None

  def __iter__(self):
    """Return generator for (key,value) pairs."""
    walk = self.first()
    while walk is not None:
      yield (walk.key(), walk.value())
      walk = walk.next()

  def closestBefore(self, key, strict=True):
    """Return iterator to position at or before the key.

    With strict=True (the default), the search looks for an item
    that has a key strictly smaller than the given one.

    With strict=False, it will return an exact match if possible, and
    otherwise the closest before.

    Will return None in the case that no earlier key is found.

    """
    walk = self._trace(key)
    if walk is None:
      return None
    if self._less(walk.key, key):
      # this is strictly smaller than key, so it must be it
      return _OrderedMap.iterator(walk)
    elif not (strict or self._less(key, walk.key)):
      # use the exact match
      return _OrderedMap.iterator(walk)
    elif walk.left is not None:
      # found an exact match, and it has lesser children
      return _OrderedMap.iterator(walk.left.subtreeMax())
    else:
      # start walking upward
      while walk is not None and not self._less(walk.key, key):
        walk = walk.parent
      if walk is not None:
        return _OrderedMap.iterator(walk)
      else:
        return None

  def closestAfter(self, key, strict=True):
    """Return iterator to position at or after the key.

    With strict=True (the default), the search looks for an item
    that has a key strictly larger than the given one.

    With strict=False, it will return an exact match if possible, and
    otherwise the closest after.

    Will return None in the case that no later key is found.

    """
    walk = self._trace(key)
    if self._less(key, walk.key):
      # this is strictly larger than key, so it must be it
      return _OrderedMap.iterator(walk)
    elif not (strict or self._less(walk.key, key)):
      # use the exact match
      return _OrderedMap.iterator(walk)
    elif walk.right is not None:
      # found an exact match, and it has greater children
      return _OrderedMap.iterator(walk.right.subtreeMin())
    else:
      # start walking upward
      while walk is not None and not self._less(key, walk.key):
        walk = walk.parent
      if walk is not None:
        return _OrderedMap.iterator(walk)
      else:
        return None

  def insert(self, key, value=None):
    """Associate key to value.

    If key exists, old value is overwritten with new.
    If key does not exist, it is added to the map.

    Return an iterator to the key's position.

    """
    walk = self._trace(key)
    if walk is None:
      self._size += 1
      self._root = _OrderedMap._node(key, value)
      return _OrderedMap.iterator(self._root)
    else:
      if self._less(key, walk.key):
        walk.left = _OrderedMap._node(key, value, walk)
        walk = walk.left
        self._insertRebalance(walk)
        self._size += 1
      elif self._less(walk.key, key):
        walk.right = _OrderedMap._node(key, value, walk)
        walk = walk.right
        self._insertRebalance(walk)
        self._size += 1
      else:
        # key exists;  overwrite old value
        walk.val = value
      return _OrderedMap.iterator(walk)

  def _insertRebalance(self, walk):
    while walk.parent is not None and walk.priority < walk.parent.priority:
      self._rotateUp(walk)

  def remove(self, posn):
    """Remove the item at the given iterator."""

    if not isinstance(posn, self.iterator):
      raise TypeError("Must provide valid iterator for remove")
    
    self._size -= 1
    walk = posn._nd
    if walk.left is None or walk.right is None:
      self._easyDelete(walk)
    else:
      # use predecessor as sub for the current node
      sub = walk.left.subtreeMax()

      # fix pointer from above
      if self._root is walk:
        self._root = sub
      elif walk is walk.parent.left:
        walk.parent.left = sub
      else:
        walk.parent.right = sub

      # relocate sub and remove walk
      if sub is not walk.left:
        # clean up below
        sub.parent.right = sub.left
        if sub.left is not None:
          sub.left.parent = sub.parent
        # sub takes over left child of walk
        sub.left = walk.left
        walk.left.parent = sub
      # sub takes over right child of walk
      sub.right = walk.right
      walk.right.parent = sub
      # sub gets new parent
      sub.parent = walk.parent
      # restore heap property from sub downward
      downward = True
      while downward:
        child = sub.left
        if sub.right is not None and (child is None or sub.right.priority < child.priority):
          child = sub.right
        if child is not None and child.priority < sub.priority:
          self._rotateUp(child)
        else:
          downward = False

  def _rotateUp(self, walk):
    """Rotate node walk up one level.
    
    Assumes that walk is not the root (but parent may be)

    """
    parent = walk.parent
    grand = parent.parent
    walk.parent = grand
    parent.parent = walk
    if parent.left is walk:
      parent.left = walk.right
      if walk.right is not None:
        walk.right.parent = parent
      walk.right = parent
    else:
      parent.right = walk.left
      if walk.left is not None:
        walk.left.parent = parent
      walk.left = parent
    if grand is None:
      self._root = walk
    else:
      if grand.left is parent:
        grand.left = walk
      else:
        grand.right = walk

  def _easyDelete(self, walk):
    """Assumes that walk is a node that has at most one child."""
    if walk.left is None:
      child = walk.right
    else:
      child = walk.left

    if child is not None:
      child.parent = walk.parent
    
    if walk.parent is None:
      self._root = child
    else:
      if walk is walk.parent.left:
        walk.parent.left = child
      else:
        walk.parent.right = child
    walk.parent = walk.left = walk.right = None   # disconnect, to be safe


  ###################################################
  ######### nested class _OrderedMap._node ##########
  class _node:
    __slots__ = ('key', 'val', 'parent', 'left', 'right', 'priority')   # optimization

    """Simple struct to represent node of the treap"""
    def __init__(self, key, value=None, parent = None, leftChild = None, rightChild = None):
      self.key = key
      self.val = value
      self.parent = parent
      self.left = leftChild
      self.right = rightChild
      self.priority = _ourRandom.random()

    def subtreeMin(self):
      """Return leftmost node of subtree."""
      walk = self
      while walk.left is not None:
        walk = walk.left
      return walk

    def subtreeMax(self):
      """Return rightmost node of subtree."""
      walk = self
      while walk.right is not None:
        walk = walk.right
      return walk

    def predecessor(self):
      """Returns node of predecessor.  Returns None if this is minimum."""
      if self.left is not None:
        return self.left.subtreeMax()
      else:
        walk = self
        while walk.parent is not None and walk.parent.left is walk:
          walk = walk.parent
        return walk.parent
        
    def successor(self):
      """Returns node of successor.  Returns None if this is maximum."""
      if self.right is not None:
        return self.right.subtreeMin()
      else:
        walk = self
        while walk.parent is not None and walk.parent.right is walk:
          walk = walk.parent
        return walk.parent

  ######### end of class _OrderedMap._node ##########

    
  ######################################################
  ######### nested class _OrderedMap.iterator ##########
  class iterator:
    """Encapsulation of a position in the map"""
    def __init__(self, node):
      self._nd = node

    def __repr__(self):
      return "Iterator[key="+repr(self.key())+' value='+repr(self.value())+"]"

    def __eq__(self, other):
      """Return True if iterators represent the same position."""
      return self._nd == other._nd

    def __ne__(self, other):
      """Return True if iterators do not represent the same position."""
      return not self._nd == other._nd

    def key(self):
      """Return key of element at this position."""
      return self._nd.key

    def value(self):
      """Return value of element at this position."""
      return self._nd.val

    def prev(self):
      """Return iterator to the previous element of the map.
         Return None if there is no predecessor."""
      other = self._nd.predecessor()
      if other is not None:
        return _OrderedMap.iterator(other)
      else:
        return None

    def next(self):
      """Return iterator to the next element of the map.
         Return None if there is no successor."""
      other = self._nd.successor()
      if other is not None:
        return _OrderedMap.iterator(other)
      else:
        return None

  ######### end of class _OrderedMap.iterator ##########


class _Hierarchy:
    """Used to maintain minimal information to track which objects are
    currently contained (directly or indirectly) on a Canvas, and to
    track the parent/child relationships between those objects.

    Technically, each object is noted as an (object,cls) pair where
    cls is the class whose _draw was called.  Typically, this will be
    the object's class, but could be a parent class for some.

    Furthermore, each object typically has only one such entry in the
    hierarchy, but with multiple inheritence (e.g. Button), there
    might be three or more different entries, one due to the original
    Button._draw call, but two subsequent due to the underlying
    Rectangle._draw and Text._draw calls.
    """
    
    def __init__(self):
        self._objects = {}       # map from obj to set of all (obj,cls) pairs
        self._relationships = {} # map from (obj.cls) pair to [parentSet, childrenDict, maxSerial]
                                 # where parentSet is set of (obj,cls) tuples,
                                 # childrenDict is dictionary mapping from (child,cls) -> serialFloat,
                                 # and maxSerial is an upper bound on the serials currently in use

    def __contains__(self, drawable):
        """Determines whether the drawable is contained in the current hierarchy."""
        return drawable in self._objects

    def newCanvas(self, canvas):
        """Adds canvas as new top-level container in the hierarchy."""
        self._objects[canvas] = set()
        self._objects[canvas].add( (canvas,Canvas) )
        self._relationships[ (canvas, Canvas) ] = [set(), {}, 0]

    def addLink(self, parentTuple, childTuple):
        """Connect child to parent.

        parentTuple and childTuple should both be of form (object,cls)
        and that parentTuple is already in this hierarchy.
        """
        self._objects.setdefault(childTuple[0], set()).add(childTuple)
        relate = self._relationships[parentTuple]
        relate[2] += 1   # update serial
        relate[1][childTuple] = relate[2]    # new child with updated serial
        self._relationships.setdefault(childTuple, [set(), {}, 0])[0].add(parentTuple)

    def removeLink(self, parentTuple, childTuple):
        """Removes the child from the parent (including the cleansing of any descendents)."""
        # remove child from parent's list of children
        parentsChildren = self._relationships[parentTuple][1]
        del self._relationships[parentTuple][1][childTuple]

        # remove parent from child's list of parents
        childsParents = self._relationships[childTuple][0]
        childsParents.remove(parentTuple)
        if not childsParents:                        # empty set
            self._recursiveRemove(childTuple)

    def findChildTuple(self, parentTuple, child):
        """For when we know the child, but not the child's appropriate "class" tag
           (because _draw was not necessarily from that class)
        """
        for k in self._relationships[parentTuple][1].keys():
            if k[0] == child:
                return k

    def getSerial(self, parentTuple, childTuple):
        return self._relationships[parentTuple][1][childTuple]

    def _recursiveRemove(self, objTuple):
        # remove association from self._objects
        objSet = self._objects[objTuple[0]]
        objSet.remove(objTuple)
        if not objSet:   # empty set
            del self._objects[objTuple[0]]

        # remove association from self._relationships
        entry = self._relationships.pop(objTuple)
        children = entry[1]
        for c in children.keys():
            childsParents = self._relationships[c][0]
            childsParents.remove(objTuple)
            if not childsParents:    # no more parents
                self._recursiveRemove(c)

    def reviseChildren(self, drawTuple, childSequence):
        """Compares the newSequence of drawable's children to sequence currently on record.

        Returns list of (child,serial) pairs for those children that require updated serial numbers.
        """
        raise NotImplementedError('reviseChildren not yet written')   # TODO

    def computeUpwardChains(self, drawable, counts = None):
        if counts is None:
            counts = {}
        if isinstance(drawable, tuple):
            tuples = [ drawable ]
        else:
            tuples = self._objects[drawable]
        
        results = []
        for t in tuples:
            self._computeUpwardChainsRecurse(results,t,counts)
            
        if _debug >= 2:
            print('ComputeUpwardChains('+str(drawable)+','+str(counts)+') returning:')
            for c in results:
                print('    '+str(tuple(c)))

        return results

    def _computeUpwardChainsRecurse(self, results, drawTuple, count):
        prevCount = count.get(drawTuple,0)
        if prevCount < _RECURSIVE_LIMIT:
            parents = self._relationships[drawTuple][0]
            if parents:
                count[drawTuple] = 1 + prevCount
                for p in parents:
                    oldSize = len(results)
                    self._computeUpwardChainsRecurse(results, p, count)
                    for k in range(oldSize, len(results)):
                        results[k].append(drawTuple)
                count[drawTuple] -= 1       # decrement count, to avoid side effects
                if count[drawTuple] == 0:
                    del count[drawTuple]
            else:
                results.append( [drawTuple] )    # "drawTuple" must represent a canvas


    def computeDownwardChains(self, drawTuple):
        """Computes all downward chians from the given starting point.

        Returns pre-order list of (chain, countDict) pairs

        Allows for cycles in chain, up to the globally determined recursive limit.
        """
        results = []
        self._computeDownwardChainsRecurse(results, drawTuple, {})
        if _debug >= 2:
            print('ComputeDownwardChains('+str(drawTuple)+') returning:')
            for c in results:
                print('    '+str(tuple(c)))
        return results

    def _computeDownwardChainsRecurse(self, results, drawTuple, count):
        """
        Returns a pre-order list of all downward chains (including all prefixes).

        Furthermore this version is given a dictionary of counts, mapping from
        drawTuple -> frequency that is presumed to have occurred
        outside the context of this call (zero if not present).

        Semantic is that there is a total cap on the number of
        occurrences of any given element, including the previous
        counts.

        Note: this function must guarantee that count is restored to
        its previous state by the end of a given call so that there
        are no lasting side effect (except perhaps by having non-keys
        end up as keys with a count of zero).
        """
        prevCount = count.get(drawTuple, 0)
        count[drawTuple] = 1 + prevCount
        results.append( ([drawTuple], dict(count)) )
        for child in self._relationships[drawTuple][1].keys():
            if count.get(child, 0) < _RECURSIVE_LIMIT:
                oldSize = len(results)
                self._computeDownwardChainsRecurse(results, child, count)
                for k in range(oldSize, len(results)):
                    results[k][0].insert(0, drawTuple)
        count[drawTuple] -= 1  # decrement count to avoid lasting effect
        if count[drawTuple] == 0:
            del count[drawTuple]

    
class _RenderedHierarchy:
    class Node:
        __slots__ = ('_chain', '_children', '_sortedChildren', '_prev', '_next', '_parent',   # optimization
                     '_depth', '_transformation', '_cumulativeTransformation', '_renderedDrawable')

        def __init__(self):
            self._chain = None
            self._children = dict()
            self._sortedChildren = _OrderedMap()
            self._prev = None
            self._next = None
            self._parent = None
            self._depth = None
            self._transformation = _Transformation()
            self._cumulativeTransformation = _Transformation()
            self._renderedDrawable = None
    
    def __init__(self):
        self._root = self.Node()
        self._first = None
        self._last = None
        self._nodeLookup = dict()
        self._nodeLookup[tuple()] = self._root
        
    def add(self, chain, depth, transformation, renderedDrawable):
        """Add a new chain to the hierarchy and return the new node.
        
        The parent chain must be present.
        """
        parentChain = chain[:-1]
        parentNode = self._nodeLookup[parentChain]
        
        # Create the new node
        newNode = self.Node()
        newNode._chain = chain
        newNode._depth = depth
        newNode._transformation = transformation
        newNode._cumulativeTransformation = parentNode._cumulativeTransformation*transformation
        newNode._renderedDrawable = renderedDrawable
        newNode._parent = parentNode

        # Link new node into structure
        self._nodeLookup[chain] = newNode
        parentNode._children[chain[-1]] = newNode
        parentNode._sortedChildren[depth] = newNode
        self._addThreads(newNode, parentNode)
        return newNode
    
    def remove(self, chain):
        """Remove a node and all of its children.
        
        A list of RenderedDrawables to be deleted is returned.
        """
        node = self._nodeLookup[chain]        
        parentChain = chain[:-1]
        parentNode = self._nodeLookup[parentChain]

        # Remove parent references and threads
        parentNode._children.pop(chain[-1])
        del parentNode._sortedChildren[node._depth]
        self._removeThreads(node, parentNode)
            
        # Find all of the RenderedDrawables to delete
        deleted = list()
        queue = [node]
        while len(queue) > 0:
            n = queue.pop()
            self._nodeLookup.pop(n._chain)
            
            if n._renderedDrawable is not None:
                deleted.append(n._renderedDrawable)
            queue.extend(n._children.values())
        
        return deleted
    
    def prev(self, node):
        """Find the previous leaf node.
        
        Precondition:    node is a leaf node
        If there is no previous node it returns None
        """
        return node._prev
    
    def next(self, node):
        """Find the next leaf node.
        
        Precondition:    node is a leaf node
        If there is no next node it returns None
        """
        return node._next
    
    def first(self, node):
        while len(node._sortedChildren) > 0:
            node = node._sortedChildren.first().value()
        return node
    
    def last(self, node):
        while len(node._sortedChildren) > 0:
            node = node._sortedChildren.last().value()
        return node
    
    def getNode(self, chain):
        return self._nodeLookup[chain]
        
    def hasChain(self, chain):
        return chain in self._nodeLookup
    
    def getDepth(self, chain):
        return self._nodeLookup[chain]._depth

    def changeDepth(self, chain, newDepth):
        node = self._nodeLookup[chain]
        oldDepth = node._depth
        if _debug >= 1.5:  print('change depth of ' + str(chain) + ' from ' + str(oldDepth) + ' to ' + str(newDepth))
        node._depth = newDepth
        parent = node._parent
        handle = parent._sortedChildren.find(oldDepth)
        prevSib = handle.prev()
        nextSib = handle.next()
        del parent._sortedChildren[oldDepth]
        parent._sortedChildren[newDepth] = node
        if (prevSib is not None and newDepth < prevSib.key()) or \
           (nextSib is not None and newDepth > nextSib.key()):
            # must re-thread relative to siblings
            if _debug >= 2.5:
                for (k,v) in iter(parent._sortedChildren):
                    print( '  child: ' + str(k) + ' ' + str(v))
            self._removeThreads(node, parent)   # detach from old location
            self._addThreads(node, parent)      # reattach in new location
            return (self.first(node), self.last(node)) # Return range of things that need to be changed
        else:
            return (None, None)
    
    def changeTransform(self, chain, newTransform):
        node = self._nodeLookup[chain]
        node._transformation = newTransform
        node._cumulativeTransformation = node._parent._cumulativeTransformation * newTransform
        
        # Propogate to children
        toFix = list(node._children.values())
        while len(toFix) > 0:
            n = toFix.pop()
            n._cumulativeTransformation = n._parent._cumulativeTransformation * n._transformation
            toFix.extend(n._children.values())
            
        return (self.first(node), self.last(node))    # Return range of things that need to be changed

    def _addThreads(self, newNode, parentNode):
        """Adjust the threads to incorporate a recently added node/subtree."""
        # Find extremes in current threading (might be subtree)
        first = self.first(newNode)
        last = self.last(newNode)

        # establish links from new tree to rest
        if len(parentNode._children) == 1:
            first._prev = parentNode._prev
            last._next = parentNode._next
            parentNode._prev = None
            parentNode._next = None
        else:
            p = parentNode
            c = newNode
            while p is not None and p._sortedChildren.first().value() == c:
                c = p
                p = p._parent

            if p is None:
                first._prev = None
                last._next = self._first
            else:
                neighbor = p._sortedChildren.find(c._depth)
                first._prev = self.last(p._sortedChildren.find(c._depth).prev().value())
                last._next = first._prev._next
        
        # establish links from rest back to new tree
        if first._prev is None:
            self._first = first
        else:
            first._prev._next = first
        if last._next is None:
            self._last = last
        else:
            last._next._prev = last
        
    def _removeThreads(self, node, parentNode):
        """Adjust the threads to disengage a node/subtree that is being moved/removed."""
        # Fix threading
        if len(parentNode._children) == 0:              # Parent is now a leaf
            parentNode._prev = self.first(node)._prev
            parentNode._next = self.last(node)._next
            if parentNode._prev is None:
                self._first = parentNode
            else:
                parentNode._prev._next = parentNode
            if parentNode._next is None:
                self._last = parentNode
            else:
                parentNode._next._prev = parentNode
        else:
            first = self.first(node)
            last = self.last(node)
            if first._prev is None:
                self._first = last._next
            else:
                first._prev._next = last._next
            if last._next is None:
                self._last = first._prev
            else:
                last._next._prev = first._prev
            
    
class _UpdateManager:
    """This is a structure to manage pending updates until they are
    ready to be passed on to the _RenderedManager.

    Internally, it is modeled upon the underlying hierarchy, but
    compressed so that it only has nodes for those elements with a
    pending update. This means that siblings are guaranteed to be
    prefix-free of each other, although they may share a commond prefix.
    """

    #------------------- inner _node class -----------------
    class _node:
        """A basic inner class for a node in the tree.

        status will be maintained either as 'stable', 'remove', or 'add'

        Frozen nodes will need to mantain two states. A "private" view
        that is the state of the object as it would appear if
        subsequently unfrozen. The "public" state is a representation
        of the state of the object at the time that it was most
        recently frozen (and thus how it should currently be rendered,
        if needed). That public view is modeled as if its entire
        subtree is unfrozen (even if those nodes have corresponding
        private nodes that are truly frozen).

        Unfrozen nodes only have a public view, which can be a mix of
        frozen and unfrozen nodes as needed.
        """

        __slots__ = ('_chain', '_publicChildren', '_privateChildren', '_publicUpdates',
                     '_privateUpdates', '_status', '_special')  # optimization

        def __init__(self, chain):
            """New node is presume 'stable' unless informed subsequently"""
            self._chain = chain
            self._publicChildren = _OrderedMap()
            self._privateChildren = None
            self._publicUpdates = {}
            self._privateUpdates = None
            self._status = 'stable'        # the default
            self._special = ''             # used for special cases with propogating private/public branches

        def isFrozen(self):
            """Is this node representing a directly frozen element.

            Note: to be distinguished from indirect freeze of an ancestor
            """
            return self._privateUpdates is not None

        def doFreeze(self):
            """Freeze a node

            _privateUpdates becomes empty dictionary.

            existing (public) children must be splintered into
            appropriate private/public components.
            """
            if self._privateUpdates is None:       # i.e., not currently frozen
                self._privateUpdates = {}
                self._privateChildren = _OrderedMap()

        def doUnfreeze(self):
            """For new unfreeze, everything in private is pushed to public."""

            # doing this first step before checking frozen, because a mirrored subtree
            # might not look frozen, even though its mirror is.  Need to note that so
            # that unfreeze is propogated later.
            if self._special != 'remove':
                self._special = 'unfreeze'      # remove trumps unfreeze
            
            if self.isFrozen():
                self._publicUpdates.update(self._privateUpdates)
                self._privateUpdates = None
                # any private updates must be converted to public
                rest = self._privateChildren
                self._privateChildren = None   # hide this before re-inserting updates
                self._resolveMirror(rest)

        def _resolveMirror(self, privateMap):
            """Send updates to public branch that were buffered in private mirror."""
            # the key is that anything that happened in private branch
            # must have happened subsequent to the time that a mirror
            # was originally created.  When getting rid of the mirror,
            # we must carefully propogate a set of updates back to the
            # public branch to reflect the sequence of events.
            #
            # Special care is needed in the case that unfreezes
            # occurred or that remove/add pairs took place, since
            # those events should cause changes to the state of the
            # public branch.
            if _debug >= 2:
                print("Within _resolveMirror on node " + str(self))
            
            for (chain, child) in list(privateMap):
                if _debug >= 3:
                    print("Resolving child " + str(child) + " with status " + child._status + " and special " + child._special)
                if child._special == 'remove':      # anything else here was after the remove
                    self._updateRecurse(chain, 'remove', {}, privateMap)
                    if child._status == 'stable':    # must have been re-added subsequently
                        self._updateRecurse(chain, 'add')
                elif child._special == 'unfreeze':  # must propogate
                    self._updateRecurse(chain, 'unfreeze')

                if child._status == 'add':
                    self._updateRecurse(chain, 'add', child._publicUpdates)
                elif child._publicUpdates:
                    self._updateRecurse(chain, 'update', child._publicUpdates)
                if child._publicChildren:
                    self._resolveMirror(child._publicChildren)   # recurse, with updates sent to this node

                if child.isFrozen():
                    self._updateRecurse(chain, 'freeze')
                    if child._privateUpdates:
                        self._updateRecurse(chain, 'update', child._privateUpdates)
                    if child._privateChildren:
                        self._resolveMirror(child._privateChildren)   # recurse, with updates sent to this node
            
        def setProperties(self, properties):
            """Properties can be any dictionary of kev/value pairs.

            This assumes that frozen status is current"""
            if self.isFrozen():
                self._privateUpdates.update(properties)
            else:
                self._publicUpdates.update(properties)

        def setBorn(self):
            """Schedule an element as newly born.

            We presume that frozen status was already set before this call.
            """
            if self._status == 'remove':
                self._status = 'stable'      # rendered already existed
            else:
                self._status = 'add'

        def setDead(self, parentMap):
            """Schedule an element to die.

            If it has not previously been rendered, then the node is
            deleted entirely as it becomes irrelevant.

            If it was previously rendered, it is scheduled to die, but
            all other pending updates are flushed since they become
            irrelevant.

            parentMap should be the _children map containing this node
            as a value.

            """
            if self._status == 'add':
                # we can go ahead and kill this right away, as well as all descendents
                # (which by definition should be new)
                del parentMap[self._chain]
            else:
                # cannot kill yet, since rendering already exists.
                # But we can clear all pending properties/updates and
                # effectively unfreze.
                self._status = self._special = 'remove'        # note well that we set _special as well
                self._publicUpdates = {}
                self._publicChildren = _OrderedMap()
                self._privateUpdates = None
                self._privateChildren = None

        def _updateRecurse(self, chain, style, properties={}, parentMap=None):
            """Note that parentMap need only be sent when style is 'remove'."""
            if _debug >= 3:
                print('_UpdateManager._node._updateRecurse called with\n    ' + '\n    '.join([str(x) for x in (self,chain,style,properties)]))
                print('  Node is currently ' + ('frozen' if self.isFrozen() else 'unfrozen'))
    
            if self._chain == chain:
                # exact match;  make the changes
                if style == 'remove':
                    self.setDead(parentMap)
                elif style == 'freeze':
                    self.doFreeze()
                elif style == 'unfreeze':
                    self.doUnfreeze()
                else:
                    # either 'update' or 'add'
                    if style == 'add':
                        self.setBorn()
                    self.setProperties(properties)
            else:
                # figure out how to recurse;  all updates go to private branch if frozen
                if self.isFrozen():
                    children = self._privateChildren
                else:
                    children = self._publicChildren
                before = children.closestBefore(chain, False)
                if before is not None:
                    val = before.key()
                    if chain[:len(val)] == val:   # prefix or exact match
                        before.value()._updateRecurse(chain, style, properties, children)
                        return
                    else:
                        after = before.next()
                else:
                    after = children.first()

                # if we reach this point, we need to make a new child,
                # check for other children that should be contained under
                # new child, then recurse (on what will be base case)
                child = _UpdateManager._node(chain)
                if _debug >= 2.5:
                    print("created new _UpdateManager._node: " + str(child) + " for chain " + str(chain))
                while after is not None and after.key()[:len(chain)] == chain:
                    relocate = after
                    after = relocate.next()
                    child._publicChildren[relocate.key()] = relocate.value()  # reinsert under new node (always public)
                    children.remove(relocate)                                 # and remove from current level
                children[chain] = child                                       # add child
                child._updateRecurse(chain, style, properties, children)

        def _flushRecurse(self, parentMap=None):
          if _debug >= 3:
              print('_flushRecurse called on node ' + str(self))
              print('isFrozen currently' + str(self.isFrozen()))
    
          if self._status != 'stable' or len(self._publicUpdates) > 0:
              # this node needs to be added/removed or has properties to push
              yield (self._chain, self._status, self._publicUpdates)
              self._publicUpdates = {}
              self._status = 'stable'
    
          # consider all public children, even if current node is frozen
          for (key,c) in list(self._publicChildren):              # use copy, since calls may mutate
              for result in c._flushRecurse(self._publicChildren):
                  yield result
    
          if parentMap is not None and not self.isFrozen():
              # this node has no private data, and all public updates will have been pushed
              # only issue is remaining (frozen) children.  Let's destroy this node, and promote
              # any remaining children in its place.
              for (_,c) in self._publicChildren:
                  parentMap[c._chain] = c            # move this node's remaining children to parent
              del parentMap[self._chain]             # and then remove this node, since flushed
     
    #------------------- end of inner _node class -----------------
                

    def __init__(self):
        """An initially empty Hierarchy.

        Initialized to have a persistent root with () chain.

        """
        self._root = self._node(())

    def update(self, chain, style, properties={}):
        """Augment the manager with the given update.

        style should be either 'add', 'remove', 'freeze', 'unfreeze', or 'update'

        For 'add' or 'update', properties should be dictionary of key/value pairs.
        Empty dicitonary should be used for remove/freeze/unfreeze.
        """
        if _debug >= 1:
            print('\n_UpdateManager.update called with\n    ' + '\n    '.join([str(x) for x in (chain,style,properties)]))
            if not isinstance(style, basestring):
                raise TypeError('style should be a string')
            if style not in ('add', 'remove', 'freeze', 'unfreeze', 'update'):
                raise ValueError('invalud style designator: ' + str(statusFlags))
            if not isinstance(properties, dict):
                raise TypeError('properties should be a dictionary')
            if style in ('remove', 'freeze', 'unfreeze') and len(properties) > 0:
                raise ValueError('Must send empty dictionary with ' + style)
        self._root._updateRecurse(chain, style, properties, self._root._publicChildren)


    def flush(self):
        """This returns a preorder generator of all updates to be rendered.

        In the process, it mutates the UpdateManager to remove nodes
        associated with objects that will presumably be deleted from
        the rendering.

        Objects yielded are (chain, status, properties)
        where status is 'add', 'remove', or 'stable' and properties is a dictionary
        """
        if _debug >= 1:
            print('_UpdateManager.flush() called')
        return self._root._flushRecurse()


class _GraphicsManager:
    def __init__(self):
        # Synchornization mechanisms
        self._state = 'Initial'                 # 'Initial', 'Running', 'Stopped' or 'Failed'
        self._commandQueue = _Queue.Queue()
        self._commandLock = _threading.RLock()  # Must be grabbed before working with command queue
        
        self._resultQueue = _Queue.Queue()
        self._functionLock = _threading.RLock()


        # Rendering engine objects

        # _frontHierarchy manages the view based on what has been sent to the command queue
        self._frontHierarchy = _Hierarchy()

        # _middleHierarchy is based on middle layer that has pulled
        # stuff off the command queue and sent to update manager.
        # When commandQueue is empty, this should match _frontHierarchy
        self._middleHierarchy = _Hierarchy()

        # _middleProperties is used to cache all of the drawable
        # properties for those objects known to the middle layer.
        # These are needed for times when the middle layer must
        # retransmit them to the update manager when adding a
        # secondary chain for existing objects
        self._middleProperties = {}     # map from Drawable -> dictionary of properties

        # _updateMangager lies between the middle and back layer.  It
        # handles batching changes as well as the semantics for
        # freezing canvases or drawables
        self._updateManager = _UpdateManager()

        # _renderedHierarchy structure is based on what has already
        # been flushed through the update manager, and hence what is
        # currently rendered at the Tk level
        self._renderedHierarchy = _RenderedHierarchy()

        # Status
        self._openCanvases = []
        self._drawParent = None
        self._drawChildren = None
        
        # Event handling
        # _handlingEvents could be Always, Yes, No or Waiting
        if _nativeThreading:
          self._handlingEvents = 'Always'
        else:
          self._handlingEvents = 'No'
        self._waitingObject = None
        self._eventQueue = _Queue.Queue()
        self._eventHandlers = dict()
        self._objectIdRegistry = dict()
        self._lastEvent = None
        self._eventLock = _threading.RLock()   # TODO lock every event thing up
            
        # Mouse
        self._mousePrevPosition = None
        self._mouseButtonDown = False

    def beginRefresh(self):
        self._commandLock.acquire()

    def completeRefresh(self, pushUpdates=True):
        # TODO:  in single-threaded, wait until LAST reentrant lock released before pushing
        if pushUpdates:
          self.addCommandToQueue(('push updates',))
          if not _nativeThreading:
              self.processCommands()
              _tkroot.update()
        self._commandLock.release()

    def addCommandToQueue(self, command):
        if self._state == 'Initial':
            self._state = 'Running'
            if _nativeThreading:
                # Start command thread
                _thread.start_new_thread(_startCommandThread, ())
                _atexit.register(_stopCommandThread)
            else:
                _initLibrary()
                _atexit.register(_exitMainThread)

        if self._state != 'Failed':
          if _debug >= 1:
              print('addCommandToQueue: ' + str(command))
          self._commandQueue.put(command)

    def _closeAll(self):
        pass # TODO

    def processCommands(self):
        MAX_TIME = 0.1
        start_time = _time.time()
        try:
            while (_time.time() - start_time) <= MAX_TIME and self._state == 'Running' and not self._commandQueue.empty():
                command = self._commandQueue.get(False)
                try:
                    self.processCommand(command)
                except GraphicsError:
                    raise
        except KeyboardInterrupt:
            raise
        except GraphicsError:
            raise
        except:     # TODO: too general?
                # Note: could happen for an empty queue
                print('Unknown graphics error has occured.  Graphics manager is shutting down.')
                print('Program must be restarted to use graphics.')
                print('If problem is repeatable, please report to bugs@cs1graphics.org.')
                self._state = 'Failed'
                self._closeAll()
                if _debug > 0:    # exit upon first error
                    _traceback.print_exc(file=_sys.stdout)
                    _sys.exit()

    def serializeDepth(self, original, parentTuple, leafTuple):
        serial = -self._middleHierarchy.getSerial(parentTuple, leafTuple)  # negated to get painter's ordering
        if isinstance(parentTuple[0], (Canvas,Layer)):
            depthKey = (original, serial)
        else:                                             # user-defined
            depthKey = (None, serial)
        return depthKey

    def processCommand(self, command):
        if _debug >= 1:
            print('')
            print('Manager executing: ' + str(command))

        # Rendering
        if command[0] == 'push updates':
            self._pushUpdates()

        # Canvases
        elif command[0] == 'create canvas':
            chain = ((command[1],Canvas),)
            self._updateManager.update(chain, 'add', command[2])
            self._middleHierarchy.newCanvas(command[1])
            if command[2]['frozen']:
                self._updateManager.update(chain, 'freeze')
                
        elif command[0] == 'close canvas':
            _tkroot.update()

        # existing object is frozen
        elif command[0] == 'freeze':
            for chain in self._middleHierarchy.computeUpwardChains(command[1]):
                self._updateManager.update(tuple(chain), 'freeze')

        # existing object is unfrozen
        elif command[0] == 'unfreeze':
            for chain in self._middleHierarchy.computeUpwardChains(command[1]):
                self._updateManager.update(tuple(chain), 'unfreeze')

        # New objects
        elif command[0] == 'object added':
            containerTuple = command[1]
            drawableTuple = command[2]
            if _debug >= 1:
                print('_middleHierarchy.addLink: ' + str(containerTuple) + ' ' + str(drawableTuple))
            self._middleHierarchy.addLink(containerTuple, drawableTuple)

            downwardChains = self._middleHierarchy.computeDownwardChains(drawableTuple)
            for d,count in downwardChains:
                leafTuple = d[-1]
                properties = dict(self._middleProperties[leafTuple[0]])   # intentional copy
                isFrozen = properties['frozen']
                if len(d) > 1:
                    # we know the parent for all such chains
                    parentTuple = d[-2]
                else:
                    parentTuple = containerTuple
                properties['depth'] = self.serializeDepth(properties['depth'], parentTuple, leafTuple)

                for u in self._middleHierarchy.computeUpwardChains(containerTuple, count):
                    tc = tuple(u + d) 

                    if _debug >= 1.5:
                        print('\nAdding chain to updateManager: ' + repr(tc))
                        print("Effective depth " + str(properties['depth']))

                    self._updateManager.update(tc, 'add', properties)   
                    if isFrozen:
                        self._updateManager(tc, 'freeze')
                        
        elif command[0] == 'object removed':
            parent = command[1]
            child = command[2]
            for c in self._middleHierarchy.computeUpwardChains(parent):
                c.append( child )
                self._updateManager.update(tuple(c), 'remove')
            if _debug >= 1:
                print('_middleHierarchy.removeLink: ' + str(parent) + ' ' + str(child))
            self._middleHierarchy.removeLink(parent,child)
            
        # Drawables
        elif command[0] == 'update':
            self._middleProperties.setdefault(command[1],{}).update(command[2])
            if command[1] in self._middleHierarchy:
                for chain in self._middleHierarchy.computeUpwardChains(command[1]):
                    if 'depth' in command[2]:
                        parentTuple = chain[-2]
                        childTuple = chain[-1]
                        command[2]['depth'] = self.serializeDepth(command[2]['depth'], parentTuple, childTuple)
                        if _debug >= 1:
                            print('Updating Effective Depth: %s' % str(command[2]['depth']))
                    self._updateManager.update(tuple(chain), 'update', command[2])
                
        elif command[0] == 'load image':
            s = command[1]
            good = True
            i = None
            try:
                if s[:7] != "base64:":
                    i = _Tkinter.PhotoImage(file=command[1])
                else:
                    data = _base64.b64decode(s[7:])
                    r = _cStringIO.StringIO(data)
                    i = _ImageTk.PhotoImage(_Image.open(r).convert('RGBA'))
            except:
                good = False

            if good:
                self._resultQueue.put( (i, i.width(), i.height()) )
            else:
                self._resultQueue.put(None)

        elif command[0] == 'convert image':
            self._resultQueue.put(_convertImage(command[1]))

        elif command[0] == 'get text size':
            self._resultQueue.put(_getTextSize(command[1], command[2]))

        elif command[0] == 'save to file':
            rc = self._renderedHierarchy.getNode( ((command[1],Canvas),) )._renderedDrawable
            rc.saveToFile(command[2], command[3])
            self._resultQueue.put(None)

    def _pushUpdates(self):
        # Loop through update manager, adjust the rendered hierarchy and rendering
        if _debug >= 1:
            print("_pushUpdates called")
        for (chain, status, properties) in self._updateManager.flush():
            if _debug >= 1:
                print('_pushUpdates: ' + str(status)+' '+str(chain)+' '+str(properties))
                if self._renderedHierarchy.hasChain(chain):
                    print('    Rendered Depth is ' + str(self._renderedHierarchy.getNode(chain)._depth))

            if status == 'add':
                assert not self._renderedHierarchy.hasChain(chain)
                current = self._renderedHierarchy.add(chain, properties['depth'], properties['transformation'], None)
                current._renderedDrawable = self._createRendered(chain, properties)
                if not isinstance(current._renderedDrawable, _RenderedCanvas) and current._renderedDrawable is not None:
                    node = current._next
                    while node is not None and node._renderedDrawable is None:
                        node = node._next
                    if node is not None and node._chain[0] == chain[0]:  # TODO: correct treatment of forest???
                        if _debug >= 1: print('Putting '+str(current._renderedDrawable)+' above '+str(node._renderedDrawable))
                        current._renderedDrawable.putAbove(node._renderedDrawable)
                    else:
                        if _debug >= 1: print('Putting '+str(current._renderedDrawable)+' at bottom')
                        current._renderedDrawable.putAbove(None)

            elif status == 'remove':
                removed = self._renderedHierarchy.remove(chain)
                for renderedDrawable in removed:
                  renderedDrawable.remove()

            elif status == 'stable':
                # Update transformation
                if 'transformation' in properties:
                    (first, last) = self._renderedHierarchy.changeTransform(chain, properties['transformation'])
                    current = first
                    while True:
                        if current._renderedDrawable is not None:
                            current._renderedDrawable.update({'transformation': current._transformation})
                        if current == last:
                            break
                        current = current._next
                    del properties['transformation']  # will not need to update this below

                # Update depth
                if 'depth' in properties:
                    (first, last) = self._renderedHierarchy.changeDepth(chain, properties['depth'])
                    if first is not None:   # something changed
                        if _debug >= 1.5: print('first, last = '+str( (first._renderedDrawable,last._renderedDrawable) ))

                        # first goal is finding an adequate anchor below this group
                        below = last._next
                        while below is not None and below._renderedDrawable is None:
                            below = below._next

                        # now place series of objects in line after each other
                        current = last
                        while current != first._prev:
                            if current._renderedDrawable is not None:
                                if below is not None:
                                    if _debug >= 1.5:
                                        print('Putting '+str(current._renderedDrawable)+' above '+str(below._renderedDrawable))
                                    current._renderedDrawable.putAbove(below._renderedDrawable)
                                else:
                                    if _debug >= 1.5:
                                        print('Putting ' + str(current._renderedDrawable) +  ' at bottom')
                                    current._renderedDrawable.putAbove(None)
                                below = current
                            current = current._prev

                # Update any other properties (beyond transformation, depth)
                if properties:
                    rd = self._renderedHierarchy.getNode(chain)._renderedDrawable
                    if rd is not None:
                        rd.update(properties)

    def _createRendered(self, chain, properties):
        subchain = chain[-1][0]
        if isinstance(subchain, Canvas):
            return _RenderedCanvas(chain, properties)
        elif isinstance(subchain, Circle):
            return _RenderedCircle(chain, properties)
        elif isinstance(subchain, Ellipse):
            return _RenderedCircle(chain, properties)          # note well: using _renderedCircle
        elif isinstance(subchain, Rectangle):                # note well: Square qualifies
            return _RenderedRectangle(chain, properties)

        # For next pair of cases, we test for more specific Polygon before Path.
        # Also, note that we render ClosedSpline as a Polygon and Spline as a Path
        elif isinstance(subchain, Polygon):
            return _RenderedPolygon(chain, properties)
        elif isinstance(subchain, Path):
            return _RenderedPath(chain, properties)

        elif isinstance(subchain, Text):
            return _RenderedText(chain, properties)
        elif isinstance(subchain, Image):
            return _RenderedImage(chain, properties)

    def executeFunction(self, command):
        # Perform a single command and return a value
        # TODO: avoid possible deadlock
        self._functionLock.acquire()
        self._commandLock.acquire()
        self.addCommandToQueue(command)
        if not _nativeThreading:
            self.processCommands()
            _tkroot.update()
        self._commandLock.release()
        result = self._resultQueue.get()
        self._functionLock.release()
        return result
        
    def addEventToQueue(self, handler, event):
        if self._handlingEvents == 'Always':
            # Start a new thread and go
            pass # TODO
        elif self._handlingEvents == 'Yes':
            self._eventQueue.put((handler,event))
        elif self._handlingEvents == 'Waiting' and event._trigger == self._waitingObject:
            self._eventQueue.put((handler,event))
        else:
            pass # Ignore the event
            
    def addHandler(self, obj, handler):
        #handlers = self._eventHandlers.get(obj, set())       
        #handlers.add(handler)
        #self._eventHandlers[obj] = handlers
        self._eventHandlers.setdefault(obj, set()).add(handler)
            
    def removeHandler(self, obj, handler):
        s = self._eventHandlers.get(obj, set())
        if handler in s:
            s.remove(handler)  # 
        else:
            raise ValueError()
            
    def processEvents(self):
        while not self._eventQueue.empty():
            (handler, event) = self._eventQueue.get(False)
            self._lastEvent = event
            if self._handlingEvents == 'Waiting':
                self._handlingEvents = 'No'
            while not self._eventQueue.empty():
                self._eventQueue.get(False)
            handler.handle(event)
        
    def wait(self, waiter):
        if self._handlingEvents == 'Always':
            lock = _threading.Lock()
            rh = _ReleaseHandler(lock)
            return rh._event
        elif self._handlingEvents == 'No':
            self.addHandler(waiter, EventHandler())
            self.mainLoop(waiter, True)
            return self._lastEvent
        
    def mainLoop(self, waiting=None, exitOnAllClosed=True):
        if waiting:
            self._handlingEvents = 'Waiting'
            self._waitingObject = waiting         
        
        while self._state == 'Running' and self._handlingEvents in ('Yes', 'Waiting'):
            _tkroot.update()
            self.processEvents()
            if exitOnAllClosed and len(_graphicsManager._openCanvases) == 0:
                break
            _time.sleep(.1)
     
      

# Events Primatives
class Event(object):
    """An event typically triggered by the user interface."""
    def __init__(self):
        self._eventType = ''
        self._x, self._y = 0, 0
        self._prevx, self._prevy = 0,0
        self._key = ''
        self._button = None
        self._trigger = None
    
    def getDescription(self):
        """Return a text description of the event.

        Possibilities include:
          'mouse click', 'mouse release', 'mouse drag', 'keyboard, 'timer', 'canvas close'
        """
        return self._eventType
    
    def getMouseLocation(self):
        """Return a Point designating the location of the mouse at the time of the event."""
        return Point(self._x, self._y)
    
    def getOldMouseLocation(self):
        """Return a Point designating the location of the mouse at the start of a mouse drag."""
        return Point(self._prevx, self._prevy)
  
    def getTrigger(self):
        """Return a reference to the object that triggered the event."""
        return self._trigger
  
    def getKey(self):
        """Return a string designating the key pressed for a keyboard event."""
        return self._key

    def getButton(self):
        """Return number of the mouse button that caused the mouse event (else None)."""
        return self._button

class EventHandler(object):
    """A base class for creating new event handlers.

    The handle method for this base class does not do anything.
    """
    def __init__(self):
        """Create a new event handler.
        
        Children of this class must call this constructor.
        """
        pass

    def handle(self, event):
        """Handle an event.
        
        Child classes must override this method, but do not need
        to call it.
        """
        pass

class _ReleaseHandler(EventHandler):
    def __init__(self, lock):
        self._lock = lock
        self._event = None
        self._lock.acquire()

    def handle(self, event):
        if event.getDescription() in ['keyboard', 'mouse click', 'canvas close']:
            self._event = event
            self._lock.release()

class _EventTrigger(object):

    def __init__(self):
        pass

    def wait(self):
        """Wait for an event to occur.

        When an event occurs, an Event instance is returned
        with information about what has happened.
        """
        return _graphicsManager.wait(self)

    def addHandler(self, handler):
        """Register an EventHandler instance with this object."""
        if not isinstance(handler, EventHandler):
            raise TypeError('Only instance of EventHandler (or child class) can handle events')
        try:
            _graphicsManager.addHandler(self, handler)  # TODO should be a on queue, not thread safe
        except ValueError:
            raise ValueError('Handler is already handling events for this object')

    def removeHandler(self, handler):
        """Unregister an EventHandler instance from this object."""
        if not isinstance(handler, EventHandler):
            raise TypeError('Parameter is not an instance of EventHandler (or child class)')
        try:
            _graphicsManager.removeHandler(self, handler)  # TODO should be a on queue, not thread safe
        except ValueError:
            raise ValueError('The handler is not currently associated with this object.')

    
class _EventThread(_threading.Thread):
    def __init__(self, handler, event):
        _threading.Thread.__init__(self)
        self._handler = handler
        self._event = event
    
    def run(self):
        self._handler.handle(self._event)

# Graphics Primatives
class Point(object):
    """Stores a two-dimensional point using Cartesian coordinates."""

    def __init__(self, initialX=0, initialY=0):
        """Create a new point instance.

        initialX   x-coordinate of the point (default 0)
        initialY   y-coordinate of the point (default 0)

        """
        if not isinstance(initialX, (int, float)):
            raise TypeError('x-coordinate must be a number')

        if not isinstance(initialY, (int, float)):
            raise TypeError('y-coordinate must be a number')

        self._x = initialX
        self._y = initialY

    def getX(self):
        """Return the x-coordinate."""
        return self._x

    def setX(self, val):
        """Set the x-coordinate to val."""
        if not isinstance(val, (int, float)):
            raise TypeError('x-coordinate must be a number')
        self._x = val

    def getY(self):
        """Return the y-coordinate."""
        return self._y

    def setY(self, val):
        """Set the y-coordinate to val."""
        if not isinstance(val, (int, float)):
            raise TypeError('y-coordinate must be a number')
        self._y = val

    def get(self):
        """Return an (x,y) tuple."""
        return self._x, self._y

    def scale(self, factor):
        """Scale the coordinates by the given factor."""
        if not isinstance(factor, (int, float)):
            raise TypeError('scaling factor must be a number')
        self._x *= factor
        self._y *= factor

    def distance(self, other):
        """Return the distance between this point and the other."""
        if not isinstance(other, Point):
            raise TypeError('other must be a Point instance')
        dx = self._x - other._x
        dy = self._y - other._y
        return _math.sqrt(dx * dx + dy * dy)

    def normalize(self):
        """Mutate the point, scaling it to distance one from the origin.

        If the point currently represents the origin, it is unchanged.

        """
        mag = self.distance( Point() )
        if mag > 0:
            self.scale(1./mag)

    def __str__(self):
        """Return a string representation of the point (e.g., '<0,0>')."""
        return '<' + str(self._x) + ',' + str(self._y) + '>'

    def __neg__(self):
        """Return a new point that is the negated version of this Point."""
        return Point(-self._x, -self._y)

    def __add__(self, other):
        """Return a new point that is the sum of this Point and the other."""
        if not isinstance(other, Point):
            raise TypeError('both operands must be Point instances')
        return Point(self._x + other._x, self._y + other._y)

    def __sub__(self, other):
        """Return a new point that is the oriented difference between the points."""
        if not isinstance(other, Point):
            raise TypeError('both operands must be Point instances')
        return Point(self._x - other._x, self._y - other._y)

    def __mul__(self, operand):
        """Return the result when multiplying the Point by an operand.

        When the operand is a scalar (i.e., an int or float), return a
        Point that has coordinates equal to the original times the factor.

        When operand is another Point, return a scalar that is the dot
        product of the two points.

        """
        if isinstance(operand, (int, float)):         # multiply by constant
            return Point(self._x * operand, self._y * operand)
        elif isinstance(operand, Point):           # dot-product
            return self._x * operand._x + self._y * operand._y
        else:
            raise TypeError('unexpected operand for multiplication')

    def __rmul__(self, operand):
        """Return the result when multiplying the Point by an operand.

        See __mul__ for details.

        """
        return self * operand

    def __xor__(self, angle):
        """Return a point instance equal to a rotated version of the original.

        angle  number of degrees of rotation

        Rotation is performed about the origin.

        """
        if not isinstance(angle, (int, float)):
            raise TypeError('angle must be a number')
        angle = _math.pi*angle/180.
        return Point(self._x * _math.cos(angle) - self._y * _math.sin(angle),
                     self._x * _math.sin(angle) + self._y * _math.cos(angle))

class _Transformation(object):
    EPSILON = 0.0000001            # arbitrary
    
    def __init__(self, value=None):
        if value:
            self._matrix = tuple(value[:4])
            self._translation = tuple(value[4:])
        else:
            self._matrix = (1., 0., 0., 1.)
            self._translation = (0., 0.)

    def  __str__(self):
        return repr(self._matrix)[:-1] + '; ' + repr(self._translation)[1:]

    def image(self, point):
        return Point(self._matrix[0]*point._x + self._matrix[1]*point._y + self._translation[0],
                     self._matrix[2]*point._x + self._matrix[3]*point._y + self._translation[1])

    def inv(self):
        detinv = 1. / self.det()
        m = ( self._matrix[3] * detinv, -self._matrix[1] * detinv,
              -self._matrix[2] * detinv, self._matrix[0] * detinv )
        t = ( -m[0]*self._translation[0] - m[1]*self._translation[1],
              -m[2]*self._translation[0] - m[3]*self._translation[1])
        return _Transformation(m+t)

    def __mul__(self, other):
        m = (self._matrix[0] * other._matrix[0] + self._matrix[1] * other._matrix[2],
             self._matrix[0] * other._matrix[1] + self._matrix[1] * other._matrix[3],
             self._matrix[2] * other._matrix[0] + self._matrix[3] * other._matrix[2],
             self._matrix[2] * other._matrix[1] + self._matrix[3] * other._matrix[3])

        p = self.image( Point(other._translation[0], other._translation[1]) )

        return _Transformation(m + (p.getX(), p.getY()))

    def det(self):
        return (self._matrix[0] * self._matrix[3] - self._matrix[1] * self._matrix[2])

    def scale(self):
        return _math.sqrt(abs(self.det()))

    def scaleAndTranslate(self):
        temp = self._matrix[0] - self._matrix[3] * (-1 if _mathMode else 1)
        return (abs(temp) <= _Transformation.EPSILON and
                abs(self._matrix[1]) <= _Transformation.EPSILON and
                abs(self._matrix[2]) <= _Transformation.EPSILON)

    def diagonalAndTranslate(self):
        return (abs(self._matrix[1]) <= _Transformation.EPSILON and
                abs(self._matrix[2]) <= _Transformation.EPSILON)

    def translateOnly(self):
        return (abs(self._matrix[1]) <= _Transformation.EPSILON and
                abs(self._matrix[2]) <= _Transformation.EPSILON and
                abs(self._matrix[0] - 1) <= _Transformation.EPSILON and
                abs(self._matrix[3] - 1) <= _Transformation.EPSILON)

class Color(object):

    """A color representation.

    A color can be specified by name or RGB value.
    'Transparent' is used to denote the lack of a color.

    See Color.AVAILABLE for a list of available color names.

    """

    _colorValues = {
        'aliceblue'            : (240,248,255), 'antiquewhite'         : (250,235,215),
        'antiquewhite1'        : (255,239,219), 'antiquewhite2'        : (238,223,204),
        'antiquewhite3'        : (205,192,176), 'antiquewhite4'        : (139,131,120),
        'aquamarine'           : (127,255,212), 'aquamarine1'          : (127,255,212),
        'aquamarine2'          : (118,238,198), 'aquamarine3'          : (102,205,170),
        'aquamarine4'          : ( 69,139,116), 'azure'                : (240,255,255),
        'azure1'               : (240,255,255), 'azure2'               : (224,238,238),
        'azure3'               : (193,205,205), 'azure4'               : (131,139,139),
        'beige'                : (245,245,220), 'bisque'               : (255,228,196),
        'bisque1'              : (255,228,196), 'bisque2'              : (238,213,183),
        'bisque3'              : (205,183,158), 'bisque4'              : (139,125,107),
        'black'                : (  0,  0,  0), 'blanchedalmond'       : (255,235,205),
        'blue'                 : (  0,  0,255), 'blue1'                : (  0,  0,255),
        'blue2'                : (  0,  0,238), 'blue3'                : (  0,  0,205),
        'blue4'                : (  0,  0,139), 'blueviolet'           : (138, 43,226),
        'brown'                : (165, 42, 42), 'brown1'               : (255, 64, 64),
        'brown2'               : (238, 59, 59), 'brown3'               : (205, 51, 51),
        'brown4'               : (139, 35, 35), 'burlywood'            : (222,184,135),
        'burlywood1'           : (255,211,155), 'burlywood2'           : (238,197,145),
        'burlywood3'           : (205,170,125), 'burlywood4'           : (139,115, 85),
        'cadetblue'            : ( 95,158,160), 'cadetblue1'           : (152,245,255),
        'cadetblue2'           : (142,229,238), 'cadetblue3'           : (122,197,205),
        'cadetblue4'           : ( 83,134,139), 'chartreuse'           : (127,255,  0),
        'chartreuse1'          : (127,255,  0), 'chartreuse2'          : (118,238,  0),
        'chartreuse3'          : (102,205,  0), 'chartreuse4'          : ( 69,139,  0),
        'chocolate'            : (210,105, 30), 'chocolate1'           : (255,127, 36),
        'chocolate2'           : (238,118, 33), 'chocolate3'           : (205,102, 29),
        'chocolate4'           : (139, 69, 19), 'coral'                : (255,127, 80),
        'coral1'               : (255,114, 86), 'coral2'               : (238,106, 80),
        'coral3'               : (205, 91, 69), 'coral4'               : (139, 62, 47),
        'cornflowerblue'       : (100,149,237), 'cornsilk'             : (255,248,220),
        'cornsilk1'            : (255,248,220), 'cornsilk2'            : (238,232,205),
        'cornsilk3'            : (205,200,177), 'cornsilk4'            : (139,136,120),
        'cyan'                 : (  0,255,255), 'cyan1'                : (  0,255,255),
        'cyan2'                : (  0,238,238), 'cyan3'                : (  0,205,205),
        'cyan4'                : (  0,139,139), 'darkblue'             : (  0,  0,139),
        'darkcyan'             : (  0,139,139), 'darkgoldenrod'        : (184,134, 11),
        'darkgoldenrod1'       : (255,185, 15), 'darkgoldenrod2'       : (238,173, 14),
        'darkgoldenrod3'       : (205,149, 12), 'darkgoldenrod4'       : (139,101,  8),
        'darkgray'             : (169,169,169), 'darkgreen'            : (  0,100,  0),
        'darkgrey'             : (169,169,169), 'darkkhaki'            : (189,183,107),
        'darkmagenta'          : (139,  0,139), 'darkolivegreen'       : ( 85,107, 47),
        'darkolivegreen1'      : (202,255,112), 'darkolivegreen2'      : (188,238,104),
        'darkolivegreen3'      : (162,205, 90), 'darkolivegreen4'      : (110,139, 61),
        'darkorange'           : (255,140,  0), 'darkorange1'          : (255,127,  0),
        'darkorange2'          : (238,118,  0), 'darkorange3'          : (205,102,  0),
        'darkorange4'          : (139, 69,  0), 'darkorchid'           : (153, 50,204),
        'darkorchid1'          : (191, 62,255), 'darkorchid2'          : (178, 58,238),
        'darkorchid3'          : (154, 50,205), 'darkorchid4'          : (104, 34,139),
        'darkred'              : (139,  0,  0), 'darksalmon'           : (233,150,122),
        'darkseagreen'         : (143,188,143), 'darkseagreen1'        : (193,255,193),
        'darkseagreen2'        : (180,238,180), 'darkseagreen3'        : (155,205,155),
        'darkseagreen4'        : (105,139,105), 'darkslateblue'        : ( 72, 61,139),
        'darkslategray'        : ( 47, 79, 79), 'darkslategray1'       : (151,255,255),
        'darkslategray2'       : (141,238,238), 'darkslategray3'       : (121,205,205),
        'darkslategray4'       : ( 82,139,139), 'darkslategrey'        : ( 47, 79, 79),
        'darkturquoise'        : (  0,206,209), 'darkviolet'           : (148,  0,211),
        'deeppink'             : (255, 20,147), 'deeppink1'            : (255, 20,147),
        'deeppink2'            : (238, 18,137), 'deeppink3'            : (205, 16,118),
        'deeppink4'            : (139, 10, 80), 'deepskyblue'          : (  0,191,255),
        'deepskyblue1'         : (  0,191,255), 'deepskyblue2'         : (  0,178,238),
        'deepskyblue3'         : (  0,154,205), 'deepskyblue4'         : (  0,104,139),
        'dimgray'              : (105,105,105), 'dimgrey'              : (105,105,105),
        'dodgerblue'           : ( 30,144,255), 'dodgerblue1'          : ( 30,144,255),
        'dodgerblue2'          : ( 28,134,238), 'dodgerblue3'          : ( 24,116,205),
        'dodgerblue4'          : ( 16, 78,139), 'firebrick'            : (178, 34, 34),
        'firebrick1'           : (255, 48, 48), 'firebrick2'           : (238, 44, 44),
        'firebrick3'           : (205, 38, 38), 'firebrick4'           : (139, 26, 26),
        'floralwhite'          : (255,250,240), 'forestgreen'          : ( 34,139, 34),
        'gainsboro'            : (220,220,220), 'ghostwhite'           : (248,248,255),
        'gold'                 : (255,215,  0), 'gold1'                : (255,215,  0),
        'gold2'                : (238,201,  0), 'gold3'                : (205,173,  0),
        'gold4'                : (139,117,  0), 'goldenrod'            : (218,165, 32),
        'goldenrod1'           : (255,193, 37), 'goldenrod2'           : (238,180, 34),
        'goldenrod3'           : (205,155, 29), 'goldenrod4'           : (139,105, 20),
        'gray'                 : (190,190,190), 'gray0'                : (  0,  0,  0),
        'gray1'                : (  3,  3,  3), 'gray10'               : ( 26, 26, 26),
        'gray100'              : (255,255,255), 'gray11'               : ( 28, 28, 28),
        'gray12'               : ( 31, 31, 31), 'gray13'               : ( 33, 33, 33),
        'gray14'               : ( 36, 36, 36), 'gray15'               : ( 38, 38, 38),
        'gray16'               : ( 41, 41, 41), 'gray17'               : ( 43, 43, 43),
        'gray18'               : ( 46, 46, 46), 'gray19'               : ( 48, 48, 48),
        'gray2'                : (  5,  5,  5), 'gray20'               : ( 51, 51, 51),
        'gray21'               : ( 54, 54, 54), 'gray22'               : ( 56, 56, 56),
        'gray23'               : ( 59, 59, 59), 'gray24'               : ( 61, 61, 61),
        'gray25'               : ( 64, 64, 64), 'gray26'               : ( 66, 66, 66),
        'gray27'               : ( 69, 69, 69), 'gray28'               : ( 71, 71, 71),
        'gray29'               : ( 74, 74, 74), 'gray3'                : (  8,  8,  8),
        'gray30'               : ( 77, 77, 77), 'gray31'               : ( 79, 79, 79),
        'gray32'               : ( 82, 82, 82), 'gray33'               : ( 84, 84, 84),
        'gray34'               : ( 87, 87, 87), 'gray35'               : ( 89, 89, 89),
        'gray36'               : ( 92, 92, 92), 'gray37'               : ( 94, 94, 94),
        'gray38'               : ( 97, 97, 97), 'gray39'               : ( 99, 99, 99),
        'gray4'                : ( 10, 10, 10), 'gray40'               : (102,102,102),
        'gray41'               : (105,105,105), 'gray42'               : (107,107,107),
        'gray43'               : (110,110,110), 'gray44'               : (112,112,112),
        'gray45'               : (115,115,115), 'gray46'               : (117,117,117),
        'gray47'               : (120,120,120), 'gray48'               : (122,122,122),
        'gray49'               : (125,125,125), 'gray5'                : ( 13, 13, 13),
        'gray50'               : (127,127,127), 'gray51'               : (130,130,130),
        'gray52'               : (133,133,133), 'gray53'               : (135,135,135),
        'gray54'               : (138,138,138), 'gray55'               : (140,140,140),
        'gray56'               : (143,143,143), 'gray57'               : (145,145,145),
        'gray58'               : (148,148,148), 'gray59'               : (150,150,150),
        'gray6'                : ( 15, 15, 15), 'gray60'               : (153,153,153),
        'gray61'               : (156,156,156), 'gray62'               : (158,158,158),
        'gray63'               : (161,161,161), 'gray64'               : (163,163,163),
        'gray65'               : (166,166,166), 'gray66'               : (168,168,168),
        'gray67'               : (171,171,171), 'gray68'               : (173,173,173),
        'gray69'               : (176,176,176), 'gray7'                : ( 18, 18, 18),
        'gray70'               : (179,179,179), 'gray71'               : (181,181,181),
        'gray72'               : (184,184,184), 'gray73'               : (186,186,186),
        'gray74'               : (189,189,189), 'gray75'               : (191,191,191),
        'gray76'               : (194,194,194), 'gray77'               : (196,196,196),
        'gray78'               : (199,199,199), 'gray79'               : (201,201,201),
        'gray8'                : ( 20, 20, 20), 'gray80'               : (204,204,204),
        'gray81'               : (207,207,207), 'gray82'               : (209,209,209),
        'gray83'               : (212,212,212), 'gray84'               : (214,214,214),
        'gray85'               : (217,217,217), 'gray86'               : (219,219,219),
        'gray87'               : (222,222,222), 'gray88'               : (224,224,224),
        'gray89'               : (227,227,227), 'gray9'                : ( 23, 23, 23),
        'gray90'               : (229,229,229), 'gray91'               : (232,232,232),
        'gray92'               : (235,235,235), 'gray93'               : (237,237,237),
        'gray94'               : (240,240,240), 'gray95'               : (242,242,242),
        'gray96'               : (245,245,245), 'gray97'               : (247,247,247),
        'gray98'               : (250,250,250), 'gray99'               : (252,252,252),
        'green'                : (  0,255,  0), 'green1'               : (  0,255,  0),
        'green2'               : (  0,238,  0), 'green3'               : (  0,205,  0),
        'green4'               : (  0,139,  0), 'greenyellow'          : (173,255, 47),
        'grey'                 : (190,190,190), 'grey0'                : (  0,  0,  0),
        'grey1'                : (  3,  3,  3), 'grey10'               : ( 26, 26, 26),
        'grey100'              : (255,255,255), 'grey11'               : ( 28, 28, 28),
        'grey12'               : ( 31, 31, 31), 'grey13'               : ( 33, 33, 33),
        'grey14'               : ( 36, 36, 36), 'grey15'               : ( 38, 38, 38),
        'grey16'               : ( 41, 41, 41), 'grey17'               : ( 43, 43, 43),
        'grey18'               : ( 46, 46, 46), 'grey19'               : ( 48, 48, 48),
        'grey2'                : (  5,  5,  5), 'grey20'               : ( 51, 51, 51),
        'grey21'               : ( 54, 54, 54), 'grey22'               : ( 56, 56, 56),
        'grey23'               : ( 59, 59, 59), 'grey24'               : ( 61, 61, 61),
        'grey25'               : ( 64, 64, 64), 'grey26'               : ( 66, 66, 66),
        'grey27'               : ( 69, 69, 69), 'grey28'               : ( 71, 71, 71),
        'grey29'               : ( 74, 74, 74), 'grey3'                : (  8,  8,  8),
        'grey30'               : ( 77, 77, 77), 'grey31'               : ( 79, 79, 79),
        'grey32'               : ( 82, 82, 82), 'grey33'               : ( 84, 84, 84),
        'grey34'               : ( 87, 87, 87), 'grey35'               : ( 89, 89, 89),
        'grey36'               : ( 92, 92, 92), 'grey37'               : ( 94, 94, 94),
        'grey38'               : ( 97, 97, 97), 'grey39'               : ( 99, 99, 99),
        'grey4'                : ( 10, 10, 10), 'grey40'               : (102,102,102),
        'grey41'               : (105,105,105), 'grey42'               : (107,107,107),
        'grey43'               : (110,110,110), 'grey44'               : (112,112,112),
        'grey45'               : (115,115,115), 'grey46'               : (117,117,117),
        'grey47'               : (120,120,120), 'grey48'               : (122,122,122),
        'grey49'               : (125,125,125), 'grey5'                : ( 13, 13, 13),
        'grey50'               : (127,127,127), 'grey51'               : (130,130,130),
        'grey52'               : (133,133,133), 'grey53'               : (135,135,135),
        'grey54'               : (138,138,138), 'grey55'               : (140,140,140),
        'grey56'               : (143,143,143), 'grey57'               : (145,145,145),
        'grey58'               : (148,148,148), 'grey59'               : (150,150,150),
        'grey6'                : ( 15, 15, 15), 'grey60'               : (153,153,153),
        'grey61'               : (156,156,156), 'grey62'               : (158,158,158),
        'grey63'               : (161,161,161), 'grey64'               : (163,163,163),
        'grey65'               : (166,166,166), 'grey66'               : (168,168,168),
        'grey67'               : (171,171,171), 'grey68'               : (173,173,173),
        'grey69'               : (176,176,176), 'grey7'                : ( 18, 18, 18),
        'grey70'               : (179,179,179), 'grey71'               : (181,181,181),
        'grey72'               : (184,184,184), 'grey73'               : (186,186,186),
        'grey74'               : (189,189,189), 'grey75'               : (191,191,191),
        'grey76'               : (194,194,194), 'grey77'               : (196,196,196),
        'grey78'               : (199,199,199), 'grey79'               : (201,201,201),
        'grey8'                : ( 20, 20, 20), 'grey80'               : (204,204,204),
        'grey81'               : (207,207,207), 'grey82'               : (209,209,209),
        'grey83'               : (212,212,212), 'grey84'               : (214,214,214),
        'grey85'               : (217,217,217), 'grey86'               : (219,219,219),
        'grey87'               : (222,222,222), 'grey88'               : (224,224,224),
        'grey89'               : (227,227,227), 'grey9'                : ( 23, 23, 23),
        'grey90'               : (229,229,229), 'grey91'               : (232,232,232),
        'grey92'               : (235,235,235), 'grey93'               : (237,237,237),
        'grey94'               : (240,240,240), 'grey95'               : (242,242,242),
        'grey96'               : (245,245,245), 'grey97'               : (247,247,247),
        'grey98'               : (250,250,250), 'grey99'               : (252,252,252),
        'honeydew'             : (240,255,240), 'honeydew1'            : (240,255,240),
        'honeydew2'            : (224,238,224), 'honeydew3'            : (193,205,193),
        'honeydew4'            : (131,139,131), 'hotpink'              : (255,105,180),
        'hotpink1'             : (255,110,180), 'hotpink2'             : (238,106,167),
        'hotpink3'             : (205, 96,144), 'hotpink4'             : (139, 58, 98),
        'indianred'            : (205, 92, 92), 'indianred1'           : (255,106,106),
        'indianred2'           : (238, 99, 99), 'indianred3'           : (205, 85, 85),
        'indianred4'           : (139, 58, 58), 'ivory'                : (255,255,240),
        'ivory1'               : (255,255,240), 'ivory2'               : (238,238,224),
        'ivory3'               : (205,205,193), 'ivory4'               : (139,139,131),
        'khaki'                : (240,230,140), 'khaki1'               : (255,246,143),
        'khaki2'               : (238,230,133), 'khaki3'               : (205,198,115),
        'khaki4'               : (139,134, 78), 'lavender'             : (230,230,250),
        'lavenderblush'        : (255,240,245), 'lavenderblush1'       : (255,240,245),
        'lavenderblush2'       : (238,224,229), 'lavenderblush3'       : (205,193,197),
        'lavenderblush4'       : (139,131,134), 'lawngreen'            : (124,252,  0),
        'lemonchiffon'         : (255,250,205), 'lemonchiffon1'        : (255,250,205),
        'lemonchiffon2'        : (238,233,191), 'lemonchiffon3'        : (205,201,165),
        'lemonchiffon4'        : (139,137,112), 'lightblue'            : (173,216,230),
        'lightblue1'           : (191,239,255), 'lightblue2'           : (178,223,238),
        'lightblue3'           : (154,192,205), 'lightblue4'           : (104,131,139),
        'lightcoral'           : (240,128,128), 'lightcyan'            : (224,255,255),
        'lightcyan1'           : (224,255,255), 'lightcyan2'           : (209,238,238),
        'lightcyan3'           : (180,205,205), 'lightcyan4'           : (122,139,139),
        'lightgoldenrod'       : (238,221,130), 'lightgoldenrod1'      : (255,236,139),
        'lightgoldenrod2'      : (238,220,130), 'lightgoldenrod3'      : (205,190,112),
        'lightgoldenrod4'      : (139,129, 76), 'lightgoldenrodyellow' : (250,250,210),
        'lightgray'            : (211,211,211), 'lightgreen'           : (144,238,144),
        'lightgrey'            : (211,211,211), 'lightpink'            : (255,182,193),
        'lightpink1'           : (255,174,185), 'lightpink2'           : (238,162,173),
        'lightpink3'           : (205,140,149), 'lightpink4'           : (139, 95,101),
        'lightsalmon'          : (255,160,122), 'lightsalmon1'         : (255,160,122),
        'lightsalmon2'         : (238,149,114), 'lightsalmon3'         : (205,129, 98),
        'lightsalmon4'         : (139, 87, 66), 'lightseagreen'        : ( 32,178,170),
        'lightskyblue'         : (135,206,250), 'lightskyblue1'        : (176,226,255),
        'lightskyblue2'        : (164,211,238), 'lightskyblue3'        : (141,182,205),
        'lightskyblue4'        : ( 96,123,139), 'lightslateblue'       : (132,112,255),
        'lightslategray'       : (119,136,153), 'lightslategrey'       : (119,136,153),
        'lightsteelblue'       : (176,196,222), 'lightsteelblue1'      : (202,225,255),
        'lightsteelblue2'      : (188,210,238), 'lightsteelblue3'      : (162,181,205),
        'lightsteelblue4'      : (110,123,139), 'lightyellow'          : (255,255,224),
        'lightyellow1'         : (255,255,224), 'lightyellow2'         : (238,238,209),
        'lightyellow3'         : (205,205,180), 'lightyellow4'         : (139,139,122),
        'limegreen'            : ( 50,205, 50), 'linen'                : (250,240,230),
        'magenta'              : (255,  0,255), 'magenta1'             : (255,  0,255),
        'magenta2'             : (238,  0,238), 'magenta3'             : (205,  0,205),
        'magenta4'             : (139,  0,139), 'maroon'               : (176, 48, 96),
        'maroon1'              : (255, 52,179), 'maroon2'              : (238, 48,167),
        'maroon3'              : (205, 41,144), 'maroon4'              : (139, 28, 98),
        'mediumaquamarine'     : (102,205,170), 'mediumblue'           : (  0,  0,205),
        'mediumorchid'         : (186, 85,211), 'mediumorchid1'        : (224,102,255),
        'mediumorchid2'        : (209, 95,238), 'mediumorchid3'        : (180, 82,205),
        'mediumorchid4'        : (122, 55,139), 'mediumpurple'         : (147,112,219),
        'mediumpurple1'        : (171,130,255), 'mediumpurple2'        : (159,121,238),
        'mediumpurple3'        : (137,104,205), 'mediumpurple4'        : ( 93, 71,139),
        'mediumseagreen'       : ( 60,179,113), 'mediumslateblue'      : (123,104,238),
        'mediumspringgreen'    : (  0,250,154), 'mediumturquoise'      : ( 72,209,204),
        'mediumvioletred'      : (199, 21,133), 'midnightblue'         : ( 25, 25,112),
        'mintcream'            : (245,255,250), 'mistyrose'            : (255,228,225),
        'mistyrose1'           : (255,228,225), 'mistyrose2'           : (238,213,210),
        'mistyrose3'           : (205,183,181), 'mistyrose4'           : (139,125,123),
        'moccasin'             : (255,228,181), 'navajowhite'          : (255,222,173),
        'navajowhite1'         : (255,222,173), 'navajowhite2'         : (238,207,161),
        'navajowhite3'         : (205,179,139), 'navajowhite4'         : (139,121, 94),
        'navy'                 : (  0,  0,128), 'navyblue'             : (  0,  0,128),
        'oldlace'              : (253,245,230), 'olivedrab'            : (107,142, 35),
        'olivedrab1'           : (192,255, 62), 'olivedrab2'           : (179,238, 58),
        'olivedrab3'           : (154,205, 50), 'olivedrab4'           : (105,139, 34),
        'orange'               : (255,165,  0), 'orange1'              : (255,165,  0),
        'orange2'              : (238,154,  0), 'orange3'              : (205,133,  0),
        'orange4'              : (139, 90,  0), 'orangered'            : (255, 69,  0),
        'orangered1'           : (255, 69,  0), 'orangered2'           : (238, 64,  0),
        'orangered3'           : (205, 55,  0), 'orangered4'           : (139, 37,  0),
        'orchid'               : (218,112,214), 'orchid1'              : (255,131,250),
        'orchid2'              : (238,122,233), 'orchid3'              : (205,105,201),
        'orchid4'              : (139, 71,137), 'palegoldenrod'        : (238,232,170),
        'palegreen'            : (152,251,152), 'palegreen1'           : (154,255,154),
        'palegreen2'           : (144,238,144), 'palegreen3'           : (124,205,124),
        'palegreen4'           : ( 84,139, 84), 'paleturquoise'        : (175,238,238),
        'paleturquoise1'       : (187,255,255), 'paleturquoise2'       : (174,238,238),
        'paleturquoise3'       : (150,205,205), 'paleturquoise4'       : (102,139,139),
        'palevioletred'        : (219,112,147), 'palevioletred1'       : (255,130,171),
        'palevioletred2'       : (238,121,159), 'palevioletred3'       : (205,104,137),
        'palevioletred4'       : (139, 71, 93), 'papayawhip'           : (255,239,213),
        'peachpuff'            : (255,218,185), 'peachpuff1'           : (255,218,185),
        'peachpuff2'           : (238,203,173), 'peachpuff3'           : (205,175,149),
        'peachpuff4'           : (139,119,101), 'peru'                 : (205,133, 63),
        'pink'                 : (255,192,203), 'pink1'                : (255,181,197),
        'pink2'                : (238,169,184), 'pink3'                : (205,145,158),
        'pink4'                : (139, 99,108), 'plum'                 : (221,160,221),
        'plum1'                : (255,187,255), 'plum2'                : (238,174,238),
        'plum3'                : (205,150,205), 'plum4'                : (139,102,139),
        'powderblue'           : (176,224,230), 'purple'               : (160, 32,240),
        'purple1'              : (155, 48,255), 'purple2'              : (145, 44,238),
        'purple3'              : (125, 38,205), 'purple4'              : ( 85, 26,139),
        'red'                  : (255,  0,  0), 'red1'                 : (255,  0,  0),
        'red2'                 : (238,  0,  0), 'red3'                 : (205,  0,  0),
        'red4'                 : (139,  0,  0), 'rosybrown'            : (188,143,143),
        'rosybrown1'           : (255,193,193), 'rosybrown2'           : (238,180,180),
        'rosybrown3'           : (205,155,155), 'rosybrown4'           : (139,105,105),
        'royalblue'            : ( 65,105,225), 'royalblue1'           : ( 72,118,255),
        'royalblue2'           : ( 67,110,238), 'royalblue3'           : ( 58, 95,205),
        'royalblue4'           : ( 39, 64,139), 'saddlebrown'          : (139, 69, 19),
        'salmon'               : (250,128,114), 'salmon1'              : (255,140,105),
        'salmon2'              : (238,130, 98), 'salmon3'              : (205,112, 84),
        'salmon4'              : (139, 76, 57), 'sandybrown'           : (244,164, 96),
        'seagreen'             : ( 46,139, 87), 'seagreen1'            : ( 84,255,159),
        'seagreen2'            : ( 78,238,148), 'seagreen3'            : ( 67,205,128),
        'seagreen4'            : ( 46,139, 87), 'seashell'             : (255,245,238),
        'seashell1'            : (255,245,238), 'seashell2'            : (238,229,222),
        'seashell3'            : (205,197,191), 'seashell4'            : (139,134,130),
        'sienna'               : (160, 82, 45), 'sienna1'              : (255,130, 71),
        'sienna2'              : (238,121, 66), 'sienna3'              : (205,104, 57),
        'sienna4'              : (139, 71, 38), 'skyblue'              : (135,206,235),
        'skyblue1'             : (135,206,255), 'skyblue2'             : (126,192,238),
        'skyblue3'             : (108,166,205), 'skyblue4'             : ( 74,112,139),
        'slateblue'            : (106, 90,205), 'slateblue1'           : (131,111,255),
        'slateblue2'           : (122,103,238), 'slateblue3'           : (105, 89,205),
        'slateblue4'           : ( 71, 60,139), 'slategray'            : (112,128,144),
        'slategray1'           : (198,226,255), 'slategray2'           : (185,211,238),
        'slategray3'           : (159,182,205), 'slategray4'           : (108,123,139),
        'slategrey'            : (112,128,144), 'snow'                 : (255,250,250),
        'snow1'                : (255,250,250), 'snow2'                : (238,233,233),
        'snow3'                : (205,201,201), 'snow4'                : (139,137,137),
        'springgreen'          : (  0,255,127), 'springgreen1'         : (  0,255,127),
        'springgreen2'         : (  0,238,118), 'springgreen3'         : (  0,205,102),
        'springgreen4'         : (  0,139, 69), 'steelblue'            : ( 70,130,180),
        'steelblue1'           : ( 99,184,255), 'steelblue2'           : ( 92,172,238),
        'steelblue3'           : ( 79,148,205), 'steelblue4'           : ( 54,100,139),
        'tan'                  : (210,180,140), 'tan1'                 : (255,165, 79),
        'tan2'                 : (238,154, 73), 'tan3'                 : (205,133, 63),
        'tan4'                 : (139, 90, 43), 'thistle'              : (216,191,216),
        'thistle1'             : (255,225,255), 'thistle2'             : (238,210,238),
        'thistle3'             : (205,181,205), 'thistle4'             : (139,123,139),
        'tomato'               : (255, 99, 71), 'tomato1'              : (255, 99, 71),
        'tomato2'              : (238, 92, 66), 'tomato3'              : (205, 79, 57),
        'tomato4'              : (139, 54, 38), 'turquoise'            : ( 64,224,208),
        'turquoise1'           : (  0,245,255), 'turquoise2'           : (  0,229,238),
        'turquoise3'           : (  0,197,205), 'turquoise4'           : (  0,134,139),
        'violet'               : (238,130,238), 'violetred'            : (208, 32,144),
        'violetred1'           : (255, 62,150), 'violetred2'           : (238, 58,140),
        'violetred3'           : (205, 50,120), 'violetred4'           : (139, 34, 82),
        'wheat'                : (245,222,179), 'wheat1'               : (255,231,186),
        'wheat2'               : (238,216,174), 'wheat3'               : (205,186,150),
        'wheat4'               : (139,126,102), 'white'                : (255,255,255),
        'whitesmoke'           : (245,245,245), 'yellow'               : (255,255,  0),
        'yellow1'              : (255,255,  0), 'yellow2'              : (238,238,  0),
        'yellow3'              : (205,205,  0), 'yellow4'              : (139,139,  0),
        'yellowgreen'          : (154,205, 50),
        }

    AVAILABLE = list(_colorValues.keys())
    AVAILABLE.sort()

    def randomColor():
        """Return a random color.

        This static method should be invoked as Color.randomColor().
        """
        return Color( (_random.randint(0, 255), _random.randint(0, 255), _random.randint(0, 255)) )
    randomColor = staticmethod(randomColor)

    def __init__(self, colorChoice='white'):
        """Create a new Color instance (default 'white').

        The parameter can be either:
             - a string with the name of the color
             - an (r,g,b) tuple
             - an existing Color instance (which will be cloned)

        """
        # we intentionally have Cavases and Drawable objects using a color
        # register with the color instance, so that when the color is
        # mutated, the object can be informed that it has changed
        # registration is for each (user,role) pair, so a fillable that
        # is using color as both fill and border is registered twice.
        self._users = set()

        if isinstance(colorChoice, basestring):
            try:
                self.setByName(colorChoice)
            except ValueError:
                raise
        elif isinstance(colorChoice, tuple):
            try:
                self.setByValue(colorChoice)
            except ValueError:
                raise
        elif isinstance(colorChoice, Color):
            self._colorName = colorChoice._colorName
            self._transparent = colorChoice._transparent
            self._colorValue = colorChoice._colorValue
        else:
            raise TypeError('invalid color specification')

    def __deepcopy__(self, memo={}):
        """This copy avoids duplicating the _users registry."""
        c = Color(self)
        memo[id(self)] = c
        return c

    def setByName(self, colorName):
        """Set the color to colorName.

        colorName   a string representing a valid name
                    ('Transparent' designates the lack of color)

        """
        if not isinstance(colorName, basestring):
            raise TypeError('string expected as color name')
        cleanName = colorName.lower().replace(' ','')
        if cleanName == 'transparent':
            if self._isCanvasBackground():
                raise ValueError('canvas background cannot be transparent')
            self._transparent = True
            self._colorValue = (0, 0, 0)
        else:
            if cleanName not in Color._colorValues:
                msg = colorName + ' is not a valid color name'
                raise ValueError(msg)
            self._colorValue = Color._colorValues[cleanName]
            self._transparent = False
        self._colorName = colorName    # use original string format
        self._informUsers()

    def getColorName(self):
        """Return the name of the color.

        If the color was set by RGB value, it returns 'Custom'.

        """
        return self._colorName

    def setByValue(self, rgbTuple):
        """Set the color to the given tuple of (red, green, blue) values."""
        if not isinstance(rgbTuple, tuple):
            raise TypeError('(r,g,b) tuple expected')
        if len(rgbTuple)!=3:
            raise ValueError('(r,g,b) tuple must have three components')
        for val in rgbTuple:
            if not isinstance(val, (int, float)):
                raise TypeError('tuple entries must be numbers')
            elif not 0 <= val <= 255:
                raise ValueError('tuple entries must be from 0 to 255')
        self._transparent = False
        self._colorName = 'Custom'
        self._colorValue = rgbTuple
        self._informUsers()

    def getColorValue(self):
        """Return a tuple of the (red, green, blue) color components."""
        return (self._colorValue[0], self._colorValue[1], self._colorValue[2])

    def isTransparent(self):
        """Return True if the current color is transparent."""
        return self._transparent

    def __repr__(self):
        """Return the name of the color, if named.

        Otherwise return the (r,g,b) value.

        """
        if self._colorName == 'Custom':
            return self._colorValue.__repr__()
        else:
            return self._colorName

    def __eq__(self, other):
        """Return true if the two colors have equivalent value."""
        return ( (self._transparent, self._colorValue) ==
                 (other._transparent, other._colorValue) )

    def __ne__(self, other):
        """Return true if the two colors do not have equivalent value."""
        return not self == other

    def _register(self, user, role):
        """Register a user with this Color instance."""
        if user not in self._users:
            self._users.add( (user,role) )

    def _unregister(self, user, role):
        """Unregister a user from this Color instance."""
        self._users.discard( (user,role) )

    def _isCanvasBackground(self):
        """Check to see if this Color instance is currently registered with a Canvas."""
        for (user,role) in self._users:
            if isinstance(user, Canvas):
                return True
        return False

    def _informUsers(self):
        """Inform registered users that the Color instance is mutated."""
        temp = Color(self)
        for (user,role) in self._users:
            user._update({role : temp})

    @staticmethod
    def _getTkColor(color):
        if color._transparent:
            return ''
        return '#%04X%04X%04X' % (256*color.getColorValue()[0], 256*color.getColorValue()[1], 256*color.getColorValue()[2])


class _GraphicsContainer(object):
    def __init__(self):
        self._contents = []

    def __contains__(self, obj):
        """Return True if obj is currently in the container; False otherwise."""
        return obj in self._contents

    def add(self, drawable):
        """Add the Drawable object to the container."""
        # not doing error checking here, as we want tailored messages for Canvas and Layer
        self._contents.append(drawable)
        if self in _graphicsManager._frontHierarchy:
            if _debug >= 2: print('adding drawable to "rendered" graphics container')
            _graphicsManager.beginRefresh()
            cacheParent = _graphicsManager._drawParent   # probably None.  But not quite sure
            cls = Canvas if isinstance(self, Canvas) else Layer    # although possible subclass of Layer
            _graphicsManager._drawParent = (self,cls)
            drawable._draw()
            _graphicsManager._drawParent = cacheParent
            _graphicsManager.completeRefresh()

    def remove(self, drawable):
        """Remove the Drawable object from the container."""
        # not doing error checking here, as we want tailored messages for Canvas and Layer
        self._contents.remove(drawable)
        if drawable in _graphicsManager._frontHierarchy:
            cls = Canvas if isinstance(self, Canvas) else Layer
            _graphicsManager.beginRefresh()
            childTuple = _graphicsManager._frontHierarchy.findChildTuple((self,cls), drawable)
            if _debug >= 1:
                print('_frontHierarchy.removeLink: ' + str( (self,cls) ) + ' ' + str(childTuple))
            _graphicsManager._frontHierarchy.removeLink((self,cls), childTuple)
            _graphicsManager.addCommandToQueue(('object removed', (self,cls), childTuple))
            _graphicsManager.completeRefresh()

    def clear(self):
        """Remove all objects from the container."""

        # Note: odd design, as we assume that any child class of this
        # has _frozen attribute defined as well as either a
        # freeze/unfreeze pair or a setAutoRefresh.  This is designed
        # specifically because Layers inherit this from Drawable
        # context while Canvas has its own autoRefresh interface

        wasFrozen = self._frozen
        if not wasFrozen:                     # temporarily freeze it
            try:
                self.freeze()                 # presumably a Layer
            except AttributeError:
                self.setAutoRefresh(False)    # presumably a Canvas

        contents = list(self._contents)       # intentional clone since remove mutates list
        for drawable in contents:
            self.remove(drawable)

        if not wasFrozen:                     # restore unfrozen state
            try:
                self.unfreeze()               # presumably a Layer
            except AttributeError:
                self.setAutoRefresh(True)     # presumably a Canvas

    def getContents(self):
        """Return a list of the container's contents, sorted by decreasing depth."""
        # this is not currently used by our code, but there for users
        return sorted(self._contents, key=Drawable.getDepth, reverse=True)

def _wrapUtility(cls):
    if _debug >= 2: print('_wrapUtility being called on class ' + str(cls))
    classDict = cls.__dict__
    if '_internalDraw' not in classDict:   # not alreadly wrapped
        if '_draw' in classDict:
            if _debug >= 2: print('_wrapUtility: wrap was required')
            internalDraw = cls._draw
            setattr(cls, '_internalDraw', internalDraw)
    
            #---------------------------------------------------------------------------
            # defining closure to wrap the original _draw while identifying proper class
            def drawClosure(self):
                # Note: cls and internalDraw taken from the closure
                if _debug >= 2: print(str(cls) + ' draw wrapper called on ' + str(self))
                parent = _graphicsManager._drawParent
                if not parent:
                    raise GraphicsError('_draw should not be directly called', True)
        
                siblings = _graphicsManager._drawChildren
                if siblings is not None:
                    siblings.append( (self,cls) )
        
                known = self in _graphicsManager._frontHierarchy        # query this before adding to hierarchy
                if _debug >= 1:
                    print('\n_frontHierarchy.addLink: ' + str(parent) + ' ' + str( (self,cls) ))

                _graphicsManager._frontHierarchy.addLink(parent, (self,cls))
                if not known:
                    _graphicsManager.addCommandToQueue(('update', self, self._getProperties())) # presend all properties
                _graphicsManager.addCommandToQueue(('object added', parent, (self,cls)))
        
                if not known:
                    if _debug >= 2: print('about to call original _draw() for ' + str(self))
                    _graphicsManager._drawParent = (self,cls)
                    internalDraw(self)           # the original wrapped function, taken from closure
                    _graphicsManager._drawParent = parent
            
                if _debug >= 2: print('draw wrapper call ending for ' + str(self))
            # end of closure
            #---------------------------------------------------------------------------
            setattr(cls, '_draw', drawClosure)

        # if _internalDraw exists, then parents are already wrapped as well,
        # but we cannot be sure of there is no _internalDraw nor _draw, so let's recurse
        for base in cls.__bases__:
            if issubclass(base, Drawable):
                _wrapUtility(base)


# Drawable Hierarchy
class Drawable(_EventTrigger):
    """An object that can be drawn to a graphics canvas."""

    def __init__(self, reference=None):
        """Create a Drawable instance.

        referencePoint  local reference point for scaling, rotating and flipping
                        (default Point(0,0) )
        """
        _EventTrigger.__init__(self)
        _wrapUtility(self.__class__)

        if reference is not None:
            if not isinstance(reference, Point):
                raise TypeError('reference point must be a Point instance')
        else:
            reference = Point()

        self._reference = reference
        self._transform = _Transformation()
        self._depth = 50
        self._frozen = False

    def __deepcopy__(self, memo={}):
        """This provides underlying support for clone()."""
        # We use Drawable.__deepcopy__ to do all the real work.
        # Subtypes can customize as needed.
        temp = self.__class__.__new__(self.__class__)
        memo[id(self)] = temp
        for k,v in self.__dict__.items():
            temp.__dict__[k] = _copy.deepcopy(v, memo)
        return temp

    # TODO: get rid of this. temporary hack for 3.0 issue and comparing chains
    def __lt__(self, other):
        return id(self) < id(other)
            
    def isFrozen(self):
        """Returns True if currently frozen; False otherwise."""
        return self._frozen
    
    def freeze(self):
        """Freeze the current object (if not already frozen).

        For an object that is already rendered, when frozen, any
        further changes to it will not be rendered until such time
        when unfrozen() is called.

        However, if unrendered, when added to a canvas or layer, this
        object will be rendered with its most current properties, even
        if currently frozen.
        """
        if not self._frozen:
            self._frozen = True
            if self in _graphicsManager._frontHierarchy:
                _graphicsManager.beginRefresh()
                _graphicsManager.addCommandToQueue(('freeze', self))
                _graphicsManager.completeRefresh()

    def unfreeze(self):
        """Unfreeze the current object (if currently frozen).

        When unfrozen, all changes that were made since the most
        recent call to freeze() will be rendered.

        """
        if self._frozen:
            self._frozen = False
            if self in _graphicsManager._frontHierarchy:
                _graphicsManager.beginRefresh()
                _graphicsManager.addCommandToQueue(('unfreeze', self))
                _graphicsManager.completeRefresh()

    def move(self, dx, dy):
        """Move the object dx units along X-axis and dy units along Y-axis.

        For the default coordinate system, positive dx is rightward and
        negative is leftward; positive dy is downard and negative is upward.
        """
        if not isinstance(dx, (int,float)):
            raise TypeError('dx must be numeric')
        if not isinstance(dy, (int,float)):
            raise TypeError('dy must be numeric')
        self._transform = _Transformation( (1.,0.,0.,1.,dx,dy)) * self._transform
        self._update({'transformation': self._transform})

    def moveTo(self, x, y):
        """Move the object to align its reference point with (x,y)"""
        if not isinstance(x, (int,float)):
            raise TypeError('x must be numeric')
        if not isinstance(y, (int,float)):
            raise TypeError('y must be numeric')
        curRef = self.getReferencePoint()
        self.move(x-curRef.getX(), y-curRef.getY())

    def rotate(self, angle):
        """Rotate the object around its current reference point.

        angle  number of degrees of clockwise rotation
        """
        if not isinstance(angle, (int,float)):
            raise TypeError('angle must be numeric')
        angle = -_math.pi*angle/180.
        p = self._localToGlobal(self._reference)
        trans = _Transformation((1.,0.,0.,1.)+p.get())
        rot = _Transformation((_math.cos(angle),_math.sin(angle),
                               -_math.sin(angle),_math.cos(angle),0.,0.))

        self._transform = trans*(rot*(trans.inv()*self._transform))
        self._update({'transformation': self._transform})

    def scale(self, factor):
        """Scale the object relative to its current reference point.

        factor      scale is multiplied by this number (must be positive)
        """
        if not isinstance(factor, (int,float)):
            raise TypeError('scaling factor must be a positive number')
        if factor <= 0:
            raise ValueError('scaling factor must be a positive number')

        p = self._localToGlobal(self._reference)
        trans = _Transformation((1.,0.,0.,1.)+p.get())
        sca = _Transformation((factor,0.,0.,factor,0.,0.))

        self._transform = trans*(sca*(trans.inv()*self._transform))
        self._update({'transformation': self._transform})

    def stretch(self, xFactor, yFactor, angle=0):
        """Stretch the shape in mutltiple direction.

        By default the x-axis is scaled by a factor of xFactor and the
        y-axis is scaled by a factor of yFactor.  The optional
        parameter rotates the directions that the streching is performed
        along.
        """
        if not isinstance(xFactor, (int,float)) or not isinstance(yFactor, (int,float)):
            raise TypeError('stretch factor must be a positive number')
        if xFactor<=0 or yFactor<=0:
            raise ValueError('stretch factor must be a positive number')

        p = self._localToGlobal(self._reference)
        trans = _Transformation((1.,0.,0.,1.)+p.get())
        rot = _Transformation((_math.cos(angle),_math.sin(angle),
                               -_math.sin(angle),_math.cos(angle),0.,0.))
        rotinv = rot.inv()
        sca = _Transformation((xFactor,0.,0.,yFactor,0.,0.))

        self._transform = trans*(rotinv*(sca*(rot*(trans.inv()*self._transform))))
        self._update({'transformation': self._transform})

    def flip(self, angle=0):
        """Flip the object reflected about its current reference point.

        By default the flip is a left-to-right flip with a vertical axis of symmetry.

        angle     a clockwise rotation of the axis of symmetry away from vertical
        """
        if not isinstance(angle, (int,float)):
            raise TypeError('angle must be numeric')

        angle = _math.pi*angle/180.
        p = self._localToGlobal(self._reference)
        trans = _Transformation((1.,0.,0.,1.)+p.get())
        rot = _Transformation((_math.cos(angle),_math.sin(angle),
                               -_math.sin(angle),_math.cos(angle),0.,0.))
        rotinv = rot.inv()
        invert = _Transformation((-1.,0.,0.,1.,0.,0.))

        self._transform = trans*(rotinv*(invert*(rot*(trans.inv()*self._transform))))
        self._update({'transformation': self._transform})

    def shear(self, shear, angle=0):
        """Shear the object relative to its current reference point.

        By default, points with the same y-coordinate as the reference point are left
        unchanged.  A point d units above the reference point is shifted d * shear
        units to the right.  The optional angle parameter rotates the axis
        that the shearing occurs along.

        angle      clockwise angle for shear
        """
        if not isinstance(shear, (int,float)):
            raise TypeError('shear factor must be numeric')
        if not isinstance(angle, (int,float)):
            raise TypeError('angle must be numeric')

        angle = _math.pi*angle/180.
        p = self._localToGlobal(self._reference)
        trans = _Transformation((1.,0.,0.,1.)+p.get())
        rot = _Transformation((_math.cos(angle),_math.sin(angle),
                               -_math.sin(angle),_math.cos(angle),0.,0.))
        rotinv = rot.inv()
        sh = _Transformation((1.,-shear,0.,1.,0.,0.))

        self._transform = trans*(rotinv*(sh*(rot*(trans.inv()*self._transform))))
        self._update({'transformation': self._transform})

    def getReferencePoint(self):
        """Return a copy of the current reference point.

        Note that mutating that copy has no effect on the Drawable object.
        """
        return self._localToGlobal(self._reference)

    def adjustReference(self, dx, dy):
        """Move the local reference point relative to its current position.

        Note that the object is not moved at all.
        """
        if not isinstance(dx, (int,float)):
            raise TypeError('dx must be numeric')
        if not isinstance(dy, (int,float)):
            raise TypeError('dy must be numeric')
        p = self._localToGlobal(self._reference)
        p = Point(p.getX()+dx, p.getY()+dy)
        self._reference = self._globalToLocal(p)

    def setDepth(self, depth):
        """Set the depth of the object.

        Objects with a higher depth will be rendered behind those with lower depths.
        """
        if not isinstance(depth, (int,float)):
            raise TypeError('depth must be numeric')
        self._depth = depth
        self._update({'depth': self._depth})

    def getDepth(self):
        """Return the depth of the object."""
        return self._depth

    def clone(self):
        """Return a duplicate of the drawable object.

        The duplicate will have the same properties as the original,
        including the sharing of color instances, but the new instance
        is not automatically added to those canvases or layers
        containing the original.
        
        """
        return _copy.deepcopy(self)

    def _localToGlobal(self, point):
        if not isinstance(point, Point):
            raise TypeError('parameter must be a Point instance')
        return self._transform.image(point)

    def _globalToLocal(self, point):
        if not isinstance(point, Point):
            raise TypeError('parameter must be a Point instance')
        return self._transform.inv().image(point)

    def _beginDraw(self):
        """Deprecated"""
        pass

    def _completeDraw(self):
        """Deprecated"""
        pass

    def _objectChanged(self):
        """Deprecated"""
        raise NotImplementedError('Deprecated.  Please see documentation for _contentsChanged()')

    def _draw(self):
        """Cause the object to be drawn (typically, the method is not called directly)."""
        raise NotImplementedError('_draw() method must be implemented for each Drawable')

    def _contentsChanged(self):
        """Designates that the composition of a (user-defined) Drawable may have changed.

        This should be called if an action has taken place that may
        effect the composition of _draw for this object, either
        because components have been re-ordered, or because components
        should be added or replaced.
        """
        cacheParent = _graphicsManager._drawParent
        cacheChildren = _graphicsManager._drawChildren
        _graphicsManager._drawParent = (self, self.__class__)    # hopefully this is the correct class
        _graphicsManager._drawChildren = []

        # important that we call _internalDraw, not _draw
        self._internalDraw()       
        _graphicsManager._frontHierarchy.reviseChildren(self, _graphicsManager._drawChildren)

        _graphicsManager._drawParent = cacheParent
        _graphicsManager._drawChildren = cacheChildren
        
    def _update(self, properties):
        if self in _graphicsManager._frontHierarchy:
            _graphicsManager.beginRefresh()
            _graphicsManager.addCommandToQueue(('update', self, properties))
            _graphicsManager.completeRefresh()

    def _getProperties(self):
        return {'transformation': self._transform, 'depth': self._depth, 'frozen' : self._frozen}

class Shape(Drawable):
    """A drawable objects that has a border."""

    def __init__(self, reference=None):
        """Construct a Shape instance.

        reference  the initial placement of the shape's reference point.
                   (default Point(0,0) )
        """
        if reference is not None and not isinstance(reference, Point):
            raise TypeError('reference point must be a Point instance')
        Drawable.__init__(self, reference)
        self._borderColor = Color('Black')
        self._borderColor._register(self, 'border color')
        self._borderWidth = 1
        self._dash = (1,0)        # solid line

    def __deepcopy__(self, memo={}):
        temp = Drawable.__deepcopy__(self, memo)
        temp._borderColor = self._borderColor     # do shallow copy
        temp._borderColor._register(temp, 'border color')
        return temp
 
    def setBorderColor(self, color):
        """
        Set the border color to a copy of the indicated color.

        The parameter can be either:
             - a string with the name of the color
             - an (r,g,b) tuple
             - an existing Color instance
        """
        if self._borderColor is not color:
            old = self._borderColor
            if isinstance(color, Color):
                self._borderColor = color
            else:
                try:
                    self._borderColor = Color(color)
                except (TypeError, ValueError):
                    raise
            old._unregister(self, 'border color')
            self._borderColor._register(self, 'border color')
            self._update({'border color' : self._borderColor})

    def getBorderColor(self):
        """Return the color of the object's border."""
        return self._borderColor

    def setBorderWidth(self, width):
        """Set the width of the border to the indicated width."""
        if not isinstance(width, (int,float)):
            raise TypeError('border width must be non-negative number')
        if width < 0:
            raise ValueError('border width cannot be negative')
        self._borderWidth = width / self._transform.scale()
        self._update({'border width': self._borderWidth})

    def getBorderWidth(self):
        """Return the width of the border."""
        return self._borderWidth * self._transform.scale()

    def setBorderDash(self, dashLength, gapLength=None):
        """Set the border to be a dashed line.

        downLength  the length of a dash
        gapLength   the length of interdash space (Default: downLength)

        For example,
          setBorderDash(3)   gives pattern:  xxx   xxx   xxx
          setBorderDash(4,1) gives pattern:  xxxx xxxx xxxx
          setBorderDash(1,4) gives pattern:  x    x    x    

        Note: gapLength of zero turns this into solid border.

        Note: some systems do not properly support dashes with borderWidth greater than 1.
        """
        if not isinstance(dashLength, (int,float)):
            raise TypeError('dash Length must be numeric')
        if dashLength <= 0:
            raise ValueError('dash Length must be positive')
        if gapLength is None:
            gapLength = dashLength
        if not isinstance(gapLength, (int,float)):
            raise TypeError('space Length must be numeric')
        if gapLength < 0:
            raise ValueError('space Length must be non-negative')
        self._dash = (dashLength, gapLength)
        self._update({'dash' : self._dash})

    def _getProperties(self):
        prop = Drawable._getProperties(self)
        prop.update({'border width' : self._borderWidth, 'border color' : Color(self._borderColor),
                     'dash' : self._dash})
        return prop

    # putting this at Shape rather than Drawable to avoid stubbing user-defined drawables
    def _draw(self): pass

class FillableShape(Shape):
    """A shape that can be filled with an interior color."""

    def __init__(self, reference=None):
        """Construct a new FillableShape instance.

        The interior color defaults to 'Transparent'.

        reference  the initial placement of the shape's reference point.
                   (default Point(0,0) )

        """
        if reference is not None and not isinstance(reference, Point):
            raise TypeError('reference point must be a Point instance')
        Shape.__init__(self, reference)
        self._fillColor = Color('Transparent')
        self._fillColor._register(self, 'fill color')

    def __deepcopy__(self, memo={}):
        temp = Shape.__deepcopy__(self, memo)
        temp._fillColor = self._fillColor     # do shallow copy
        temp._fillColor._register(temp, 'fill color')
        return temp
 
    def setFillColor(self, color):
        """Set the interior color of the shape to the color.

        The parameter can be either:
             - a string with the name of the color
             - an (r,g,b) tuple
             - an existing Color instance

        """
        if self._fillColor is not color:
            old = self._fillColor
            if isinstance(color, Color):
                self._fillColor = color
            else:
                try:
                    self._fillColor = Color(color)
                except (TypeError, ValueError):
                    raise

            old._unregister(self, 'fill color')
            self._fillColor._register(self, 'fill color')
            self._update({'fill color': self._fillColor})

    def getFillColor(self):
        """Return the color of the shape's interior."""
        return self._fillColor

    def _getProperties(self):
        prop = Shape._getProperties(self)
        prop['fill color'] = Color(self._fillColor)
        return prop

# Canvas class
class Canvas(_GraphicsContainer, _EventTrigger):
    """A window that can be drawn upon."""

    def __init__(self, w=200, h=200, bgColor=None, title='Graphics canvas', autoRefresh=True):
        """Create a new drawing canvas.

        A new canvas will be created.
            w             width of drawing area (default 200)
            h             height of drawing area (default 200)
            bgColor       color of the background (default 'White')
            title         window title (default 'Graphics Canvas')
            autoRefresh   whether auto-refresh mode is used (default True)

        """
        _GraphicsContainer.__init__(self)
        _EventTrigger.__init__(self)

        if not bgColor:
            bgColor = 'white'

        if not isinstance(w, (int,float)):
            raise TypeError('width must be numeric')
        if not isinstance(h, (int,float)):
            raise TypeError('height must be numeric')
        if not isinstance(title, basestring):
            raise TypeError('title must be a string')
        if not isinstance(autoRefresh, bool):
            raise TypeError('autoRefresh flag must be a boolean value')

        if isinstance(bgColor, Color):
            self._backgroundColor = bgColor
        else:
            try:
                self._backgroundColor = Color(bgColor)
            except (TypeError,ValueError):
                raise
        if Color(self._backgroundColor) == Color('transparent'):
            raise ValueError('canvas background cannot be transparent')
        self._backgroundColor._register(self, 'background color')

        if not _mathMode:
            self._transform = _Transformation()
        else:
            self._transform = _Transformation((1,0,0,-1,0,h))
        self._width = w
        self._height = h
        self._title = title
        self._canvasOpen = True
        self._mouseCoordinates = Point(0,0)
        self._animation = None
        self._frozen = False     # want initial rendering with title/size/color even if not autoRefresh
        self._reference = Point()  # TODO: hack because of use in getting event coordinates
        _graphicsManager._openCanvases.append(self)
        _graphicsManager._frontHierarchy.newCanvas(self)
        _graphicsManager.beginRefresh()
        _graphicsManager.addCommandToQueue(('create canvas', self, self._getProperties()))
        _graphicsManager.completeRefresh()
        if not autoRefresh:                # turn off auto-refresh before continuing
            self.setAutoRefresh(False)

    # TODO: get rid of this. temporary hack for 3.0 issue and comparing chains
    def __lt__(self, other):
        return id(self) < id(other)
            
    def _update(self, properties):
        _graphicsManager.beginRefresh()
        _graphicsManager.addCommandToQueue(('update', self, properties))
        _graphicsManager.completeRefresh()

    def _getProperties(self):
        # Note: using depth of (0,id(self)) to ensure uniqueness among canvases
        return { 'width': self._width, 'height': self._height, 'background color': Color(self._backgroundColor),
                 'title': self._title, 'transformation': self._transform, 'depth': (0,id(self)),
                 'frozen' : self._frozen }

    def getAutoRefresh(self):
        """Queries current state of the auto-refresh mode.

        Returns True if auto-refresh is currently set; False otherwise.

        """
        return not self._frozen

    def refresh(self):
        if self._frozen:                          # otherwise irrelevant
            # force a flush and then re-freeeze
            self.setAutoRefresh(True)
            self.setAutoRefresh(False)
        
    def setAutoRefresh(self, autoRefresh=True):
        """Change the auto-refresh mode.

        When True (the default), every change to the canvas or to an
             object drawn upon the canvas will be immediately rendered to
             the screen.

        When False, all changes are recorded internally, yet not shown
             on the screen until the next subsequent call to the refresh()
             method of this canvas.  This allows multiple changes to be
             buffered and rendered all at once.

        """
        if not isinstance(autoRefresh, bool):
            raise TypeError('autoRefresh flag should be a bool')

        if autoRefresh == self._frozen:          # if autoRefresh != self.getAutoRefresh()
            self._frozen = not autoRefresh
            cmd = 'unfreeze' if autoRefresh else 'freeze'
            _graphicsManager.beginRefresh()
            _graphicsManager.addCommandToQueue((cmd, self))
            _graphicsManager.completeRefresh()

    def setBackgroundColor(self, color):
        """Set the background color.

        The parameter can be either:
             - a string with the name of the color
             - an (r,g,b) tuple
             - an existing Color instance

        """
        if self._backgroundColor is not color:
            oldColor = self._backgroundColor
            if Color(color) == Color('transparent'):
                raise ValueError('canvas background cannot be transparent')
            if isinstance(color, Color):
                self._backgroundColor = color
            else:
                try:
                    self._backgroundColor = Color(color)
                except (TypeError, ValueError):
                    raise
            oldColor._unregister(self, 'background color')
            self._backgroundColor._register(self, 'background color')
            self._update({'background color' : Color(self._backgroundColor)})

    def getBackgroundColor(self):
        """Return the background color as a Color instance."""
        return self._backgroundColor

    def setWidth(self, w):
        """Reset the canvas width to w."""
        if not isinstance(w, (int,float)):
            raise TypeError('width must be numeric value')
        if w <= 0:
            raise ValueError('width must be positive')
        self._width = w
        self._update( {'width' : w } )

    def getWidth(self):
        """Return the width of the canvas."""
        return self._width

    def setHeight(self, h):
        """Reset the canvas height to h."""
        if not isinstance(h, (int,float)):
            raise TypeError('height must be numeric value')
        if h <= 0:
            raise ValueError('height must be positive')

        if _mathMode:
            delta = self._height - h
            self._height = h
            self._transform = self._transform * _Transformation( (1,0,0,1,0,delta) )
            self._update( {'height' : h , 'transformation' : self._transform} )
        else:
            self._height = h
            self._update( {'height' : h } )

    def getHeight(self):
        """Return the height of the canvas."""
        return self._height

    def setTitle(self, title):
        """Set the title for the canvas window to given string."""
        if not isinstance(title, basestring):
            raise TypeError('title must be a string')
        self._title = title
        self._update( {'title' : title } )

    def getTitle(self):
        """Return the title of the window."""
        return self._title

    def open(self):
        """Opens a graphic window (if not already open).

        The window can be closed with a subsequent call to close().
        """
        if not self._canvasOpen:
            self._update( {'visible' : True } )
            self._canvasOpen = True
            _graphicsManager._openCanvases.append(self)

    def close(self):
        """Close the canvas window (if not already closed).

        The window can be reopened with a subsequent call to open().
        """
        if self._canvasOpen:
            self._update( {'visible' : False } )
            self._canvasOpen = False
            _graphicsManager._openCanvases.remove(self)

    def add(self, drawable):
        """Add the Drawable object to the canvas."""
        if not isinstance(drawable, Drawable):
            raise TypeError('only Drawable objects can be added to a Canvas')
        if drawable in self._contents:
            raise ValueError('object already on the Canvas')
        if '_transform' not in vars(drawable):
            raise Exception('Drawable instance not properly initialized (was parent constructor called?)')
        try:
            drawable._draw
        except AttributeError:
            raise Exception('child class of Drawable must provide a _draw method')

        if _debug >= 1: print('\nCall to Canvas.add with self='+str(self)+' drawable='+str(drawable))
        _GraphicsContainer.add(self, drawable)
        
    def remove(self, drawable):
        """Remove the drawable object from the canvas."""
        if drawable not in self._contents:
          raise ValueError('Object not currently on the Canvas')
        _GraphicsContainer.remove(self,drawable)

    def setView(self, lowerLeft, upperRight):
        """Set the coordinates for the lower-left corner and upper-right corners of the canvas.

        lowerLeft and upperRight are Point instances storing the coordinates of the corners.
        """
        if not isinstance(lowerLeft, Point) or not isinstance(upperRight, Point):
            raise TypeError('lowerLeft and upperRight must be Point instances')
        if lowerLeft.getX() == upperRight.getX() or lowerLeft.getY() == upperRight.getY():
            raise ValueError('Lower left and upper right corners must have different x and y coordinates.')

        xScale = float(self.getWidth())/(upperRight.getX()-lowerLeft.getX())
        yScale = -float(self.getHeight())/(upperRight.getY()-lowerLeft.getY())
        xTrans = -xScale*lowerLeft.getX()
        yTrans = self.getHeight() - yScale*lowerLeft.getY()

        self._transform = _Transformation( (xScale,0,0,yScale,xTrans,yTrans) )
        self._update( {'transformation' : self._transform} )

    def zoomView(self, factor, fixedPoint=None):
        """Scales the coordinate system for the canvas about the given fixed point.

        factor      multiplicative zoom factor (must be positive number)
        fixedPoint  the fixed point for the zoom in local coordinates
                    (default center of current view)

        """
        if not isinstance(factor, (int,float)):
            raise TypeError('zoom factor must be a positive number')
        if factor <= 0:
            raise ValueError('zoom factor must be a positive number')
        if fixedPoint is not None:
            if not isinstance(fixedPoint, Point):
                raise TypeError('fixedPoint must be specified as a Point instance')
        else:
            fixedPoint = self._transform.inv().image(Point(self.getWidth()/2., self.getHeight()/2.))

        self._transform = self._transform * _Transformation( (factor,0,0,factor,
            fixedPoint.getX() * (1-factor), fixedPoint.getY()*(1-factor)))

        self._update( {'transformation' : self._transform} )

    def rotateView(self, angle, fixedPoint=None):
        """Rotates the coordinate system of the canvas about the given fixed point.

        angle       number of degrees of clockwise rotation
        fixedPoint  the fixed point for the rotation in local coordinates
                    (default center of current view)

        """
        if not isinstance(angle, (int,float)):
            raise TypeError('angle must be numeric')
        if fixedPoint is None:
            fixedPoint = self._transform.inv().image(Point(self.getWidth()/2., self.getHeight()/2.))
        if not isinstance(fixedPoint, Point):
            raise TypeError('fixedPoint must be specified as a Point instance')

        if not isinstance(fixedPoint, Point):
            raise TypeError('fixedPoint must be specified as a Point instance')

        translation = _Transformation( (1,0,0,1,fixedPoint.getX(),fixedPoint.getY()) )
        angle = -_math.pi*angle/180.
        rot = _Transformation((_math.cos(angle),_math.sin(angle),
                               -_math.sin(angle),_math.cos(angle),0.,0.))
        self._transform = self._transform * translation * rot * translation.inv()
        self._update( {'transformation' : self._transform} )

    def translateView(self, lowerLeft):
        """Translates the viewable portion of the canvas's coordinate system.

        lowerLeft  the Point in the coordinate system that should be aligned with the
                   lower-left corner of the Canvas window.
        """
        if not isinstance(lowerLeft, Point):
            raise TypeError('lowerLeft must be specified as a Point instance')

        delta = self._transform.inv().image(Point(0,self.getHeight())) + (-1)*lowerLeft
        translation = _Transformation( (1,0,0,1,delta.getX(),delta.getY()) )
        self._transform = self._transform * translation
        self._update( {'transformation' : self._transform} )

    def saveToFile(self, filename):
        """Save a picture of the current canvas to a file.

        The filename extension must be a supported file type.
        The standard extentions are either .eps or .ps.
        
        If the Python Imaging Library is installed then addition
        supported file types are: .gif, .jpg, .jpeg, .png
        """
        if not isinstance(filename, str):
            raise TypeError('filename must be a string')
        if '.' not in filename:
            raise ValueError('filename extension should indicate file type')
        ext = filename.split('.')[-1].lower()
        if not _pilAvailable:
            choices = ('eps', 'ps')
        else:
            choices = ('eps', 'ps', 'gif', 'jpg', 'jpeg', 'png')
        if ext not in choices:
            raise ValueError('Unsupported file type. Choices: ' + ' '.join(choices))

        if ext in ('eps','ps'):
            epsFilename = filename
        else:
            fd, epsFilename = _tempfile.mkstemp('.eps')
            _os.close(fd)
        
        _graphicsManager.executeFunction( ('save to file', self, epsFilename,
                                           self.getBackgroundColor()) )

        if ext not in ('eps','ps'):  # Use PIL to convert
            image = _Image.open(epsFilename).convert('RGBA')
            image.save(filename)
            _os.remove(epsFilename)
            
    def getMouseCoordinates(self):
        """Return the current coordinate of the mouse."""
        return self._mouseCoordinates

class _RenderedCanvas(object):
    def __init__(self, chain, properties):
        if _debug >= 1: print('Creating _RenderedCanvas')
        self._parent = chain[-1][0]
        self._tkWin = _Tkinter.Toplevel()
        self._tkWin.protocol('WM_DELETE_WINDOW', self._parent.close)
        self._tkWin.title(properties['title'])
        self._w = properties['width']
        self._h = properties['height']
        self._canvas = _Tkinter.Canvas(self._tkWin, width=self._w, height=self._h,
                                       highlightthickness=0,
                                       background=Color._getTkColor(properties['background color']))
        self._canvas.pack(expand=False, side=_Tkinter.TOP)
        self._tkWin.resizable(0,0)
        
        # Setup function to deal with events
        callback = lambda event : self._handleEvent(event)
        self._canvas.bind('<Button>', callback)
        self._canvas.bind('<ButtonRelease>', callback)
        self._canvas.bind('<Key>', callback)
        self._canvas.bind('<Motion>', callback)
        self._canvas.bind('<Enter>', callback)
        self._canvas.focus_set()

    def update(self, properties):
        if 'title' in properties:
            self._tkWin.title(properties['title'])
        if 'width' in properties:
            self._w = properties['width']
            self._canvas.config(width=self._w)
        if 'height' in properties:
            self._h = properties['height']
            self._canvas.config(height=self._h)
        if 'background color' in properties:
            self._canvas.config(background=Color._getTkColor(properties['background color']))
        if 'visible' in properties:
            if not properties['visible']:
                self._tkWin.withdraw()
            else:
                self._tkWin.deiconify()

    def saveToFile(self, filename, bgcolor):
        # add rectangle to simulate background color
        fakeBG = self._canvas.create_polygon((0,0), (self._w,0), (self._w,self._h), (0,self._h),
                                             fill=Color._getTkColor(bgcolor),outline='')
        self._canvas.lower(fakeBG)
        try:
            self._canvas.postscript(file=filename)
        except KeyboardInterrupt:
            raise
        except:
            pass
        self._canvas.delete(fakeBG)
        
    def _handleEvent(self, event):
        # Create the event
        e = Event()
        if not _graphicsManager._mousePrevPosition:
            e._prevx, e._prevy = event.x, event.y
        else:
            e._prevx, e._prevy = _graphicsManager._mousePrevPosition[0], _graphicsManager._mousePrevPosition[1]
        _graphicsManager._mousePrevPosition = (int(event.x), int(event.y))
        e._x, e._y = event.x, event.y
        
        # Set the mouse coordinates
        # TODO must deal with tranformations for top level on all coordinates
        self._parent._mouseCoordinates = Point(e._x, e._y)
        
        if int(event.type) == 2:   # Keypress
            e._eventType = 'keyboard'
            if event.char:
                e._key = event.char
            else:
                if event.keysym == 'Return':
                    e._key = '\n'
                elif event.keysym == 'BackSpace':
                    e._key = '\b'
                elif event.keysym == 'Tab':
                    e._key = '\t'
                else:
                    return  # ignore this event.
        elif int(event.type) == 4: # Mouse click
            e._eventType = 'mouse click'
            e._button = event.num
            _graphicsManager._mouseButtonDown = True
        elif int(event.type) == 5: # Mouse release
            e._eventType = 'mouse release'
            e._button = event.num
            _graphicsManager._mouseButtonDown = False
        elif int(event.type) == 6: # Mouse move
            self._canvas._mouseCoordinates = Point(e._x, e._y)
            if _graphicsManager._mouseButtonDown:
                e._eventType = 'mouse drag'
            else:
                return
        else:
            return       
          
          
        # Find the shape where the event occurred:
        tkIds = self._canvas.find_overlapping(event.x, event.y, event.x, event.y)
        if len(tkIds) > 0:
            chain = _graphicsManager._objectIdRegistry[(self._canvas, tkIds[-1])]._chain
        else:          
            chain = ((self._parent,Canvas),)

        for i in range(len(chain),0,-1):
            subchain = chain[:i]
            e._trigger = subchain[-1][0]
            for h in _graphicsManager._eventHandlers.get(e._trigger,set()):
                transformedEvent = _copy.copy(e)
                cumInv = _graphicsManager._renderedHierarchy.getNode(subchain)._cumulativeTransformation.inv()
                local = _graphicsManager._renderedHierarchy.getNode(subchain)._transformation
                trans = local.image(e._trigger._reference)  # TODO make property; not thread safe
                p = local.image(cumInv.image(Point(e._x, e._y)))
                transformedEvent._x = p._x - trans._x
                transformedEvent._y = p._y - trans._y
                _graphicsManager.addEventToQueue(h, transformedEvent)


# Layer class
class Layer(Drawable, _GraphicsContainer):
    """A composite that represents a group of shapes as a single drawable object.

    Objects are placed onto the layer relative to the coordinate
    system of the layer itself.  The layer can then be placed onto a
    canvas (or even onto another layer).

    """
    def __init__(self):
        """Construct a new Layer instance.

        The layer is initially empty.

        The reference point of that layer is initially the origin in
        its own coordinate system, (0,0).

        """
        Drawable.__init__(self)
        _GraphicsContainer.__init__(self)
        self._final = False

    def finalize(self):
        """Finalize the layer.

        Once finalized, objects can no longer be added or deleted.

        """
        self._final = True
        
    def add(self, drawable):
        """Add the Drawable object to the layer."""
        if _debug >= 1: print('\nCall to Layer.add with self='+str(self)+' drawable='+str(drawable))
        if self._final:
            raise Exception('cannot add objects once finalized')
        if not isinstance(drawable, Drawable):
            raise TypeError('parameter must be an instance of a Drawable object')
        if drawable in self._contents:
            raise ValueError('object is already on the Layer')
        if '_transform' not in vars(drawable):
            raise Exception('Drawable not properly initialized (was parent constructor called?)')
        try:
            drawable._draw
        except KeyboardInterrupt:
            raise
        except:
            raise Exception('Drawable class must have a _draw method')

        _GraphicsContainer.add(self, drawable)

    def remove(self, drawable):
        """Remove the Drawable object from the layer.

        A ValueError is raised if the drawable is not currently in the layer.

        """
        if self._final:
            raise Exception('cannot remove objects once finalized')
        if drawable not in self._contents:
            raise ValueError('object not currently on the Layer')

        _GraphicsContainer.remove(self,drawable)

    def clear(self):
        """Remove all objects from the layer."""
        if self._final:
            raise Exception('cannot remove objects once finalized')
        _GraphicsContainer.clear(self)

    def _draw(self):
        for shape in self._contents:   # according to inserted order
            shape._draw()


class Circle(FillableShape):
    """A circle that can be drawn to a canvas."""
    def __init__(self, radius=10, centerPt=None):
        """Construct a new instance of Circle.

        radius    the circle's radius (default 10)
        centerPt  a Point representing the placement of the circle's center
                  (default Point(0,0) )

        The reference point for a circle is originally its center.

        """
        if not isinstance(radius, (int,float)):
            raise TypeError('radius must be numeric')
        if radius <= 0:
            raise ValueError("radius must be positive")
        if centerPt and not isinstance(centerPt, Point):
            raise TypeError("circle's center must be specified as a Point")

        FillableShape.__init__(self)
        if not centerPt:
            centerPt = Point()
        oldBorderWidth = self.getBorderWidth()
        self._transform = _Transformation( (radius,0.,0.,radius,centerPt.getX(),centerPt.getY()) )
        self._borderWidth = oldBorderWidth / self._transform.scale()

    def setRadius(self, r):
        """Set the radius of the circle to r."""
        if not isinstance(r, (int,float)):
            raise TypeError('radius must be numeric')
        if r <= 0:
            raise ValueError("radius must be positive")

        factor = float(r)/self.getRadius()
        oldBorderWidth = self.getBorderWidth()
        self._transform = self._transform * _Transformation((factor,0.,0.,factor,0.,0.))
        self._borderWidth = oldBorderWidth / self._transform.scale()
        self._update({'transformation': self._transform, 'border width': self._borderWidth})

    def getRadius(self):
        """Return the radius of the circle."""
        return _math.sqrt(self._transform._matrix[0]**2 + self._transform._matrix[1]**2)

class Ellipse(FillableShape):
    """A ellipse that can be drawn to a canvas."""

    def __init__(self, w=10, h=10, centerPt=None):
        """Construct a new instance of Circle.

        w         the ellipse's width (default 10)
        h         the ellipse's height (default 10)
        centerPt  a Point representing the placement of the circle's center
                  (default Point(0,0) )

        The reference point for a ellipse is originally its center.

        """
        if not isinstance(w, (int,float)):
            raise TypeError('width must be numeric')
        if w <= 0:
            raise ValueError('width must be positive')
        if not isinstance(h, (int,float)):
            raise TypeError('height must be numeric')
        if h <= 0:
            raise ValueError('height must be positive')
        if centerPt and not isinstance(centerPt, Point):
            raise TypeError("center must be specified as a Point")

        FillableShape.__init__(self) # intentionally not sending center
        if not centerPt:
            centerPt = Point()
        oldBorderWidth = self.getBorderWidth()
        self._transform = _Transformation( (.5*w, 0., 0., .5*h, centerPt.getX(), centerPt.getY()) )
        self._borderWidth = oldBorderWidth / self._transform.scale()

    def getWidth(self):
        """Return the width of the ellipse."""
        return 2*_math.sqrt(self._transform._matrix[0]**2 + self._transform._matrix[2]**2)

    def getHeight(self):
        """Return the height of the ellipse."""
        return 2*_math.sqrt(self._transform._matrix[1]**2 + self._transform._matrix[3]**2)

    def setWidth(self, w):
        """Set the width of the ellipse to w."""
        if not isinstance(w, (int,float)):
            raise TypeError('width must be numeric')
        if w <= 0:
            raise ValueError("width must be positive")

        factor = float(w)/self.getWidth()
        oldBorderWidth = self.getBorderWidth()
        self._transform = self._transform * _Transformation((factor,0.,0.,1.,0.,0.))
        self._borderWidth = oldBorderWidth / self._transform.scale()
        self._update({'transformation': self._transform, 'border width': self._borderWidth})

    def setHeight(self, h):
        """Set the height of the ellipse to h."""
        if not isinstance(h, (int,float)):
            raise TypeError('height must be numeric')
        if h <= 0:
            raise ValueError("height must be numeric")

        factor = float(h)/self.getHeight()
        oldBorderWidth = self.getBorderWidth()
        self._transform = self._transform * _Transformation((1.,0.,0.,factor,0.,0.))
        self._borderWidth = oldBorderWidth / self._transform.scale()
        self._update({'transformation': self._transform, 'border width': self._borderWidth})

class Rectangle(FillableShape):
    """A rectangle that can be drawn to the canvas."""

    def __init__(self, w=20, h=10, centerPt=None):
        """
        Construct a new instance of a Rectangle.

        The reference point for a rectangle is its center.

        w         the width of the rectangle (default 20)
        h         the height of the rectangle (default 10)
        centerPt  a Point representing the placement of the rectangle's center
                  (default Point(0,0) )

        """
        if not isinstance(w, (int,float)):
            raise TypeError('width must be numericr')
        if w <= 0:
            raise ValueError('width must be positive')
        if not isinstance(h, (int,float)):
            raise TypeError('height must be numeric')
        if h <= 0:
            raise ValueError('height must be positive')
        if centerPt and not isinstance(centerPt, Point):
            raise TypeError('center must be specified as a Point')

        FillableShape.__init__(self)  # intentionally not sending center point
        if not centerPt:
            centerPt = Point(0,0)
        oldBorderWidth = self.getBorderWidth()
        self._transform = _Transformation( (w, 0., 0., h, centerPt.getX(), centerPt.getY()) )
        self._borderWidth = oldBorderWidth / self._transform.scale()

    def getWidth(self):
        """Return the width of the rectangle."""
        return _math.sqrt(self._transform._matrix[0]**2 + self._transform._matrix[2]**2)

    def getHeight(self):
        """Return the height of the rectangle."""
        return _math.sqrt(self._transform._matrix[1]**2 + self._transform._matrix[3]**2)

    def setWidth(self, w):
        """Set the width of the rectangle to w."""
        if not isinstance(w, (int,float)):
            raise TypeError('width must be a positive number')
        if w <= 0:
            raise ValueError("width must be positive")
        factor = float(w) / self.getWidth()
        oldBorderWidth = self.getBorderWidth()
        p = self._localToGlobal(self._reference)
        trans = _Transformation((1.,0.,0.,1.)+p.get())
        sca = _Transformation((factor,0.,0.,1.,0.,0.))
        self._transform = trans*(sca*(trans.inv()*self._transform))
        self._borderWidth = oldBorderWidth / self._transform.scale()
        self._update({'transformation': self._transform, 'border width': self._borderWidth})

    def setHeight(self, h):
        """Set the height of the rectangle to h."""
        if not isinstance(h, (int,float)):
            raise TypeError('height must be a positive number')
        if h <= 0:
            raise ValueError("height must be positive")
        factor = float(h) / self.getHeight()
        oldBorderWidth = self.getBorderWidth()
        p = self._localToGlobal(self._reference)
        trans = _Transformation((1.,0.,0.,1.)+p.get())
        sca = _Transformation((1.,0.,0.,factor,0.,0.))
        self._transform = trans*(sca*(trans.inv()*self._transform))
        self._borderWidth = oldBorderWidth / self._transform.scale()
        self._update({'transformation': self._transform, 'border width': self._borderWidth})

class Square(Rectangle):
    """A square that can be drawn to the canvas."""

    def __init__(self, size=10, centerPt=None):
        """
        Construct a new Square instance.

        The reference point for a square is its center.

        size      the dimension of the square (default 10)
        centerPt  a Point representing the placement of the rectangle's center
                  (defaults Point(0,0) )

        """
        if not isinstance(size, (int,float)):
            raise TypeError('size must be numeric')
        if size <= 0:
            raise ValueError('size must be positive')
        if centerPt and not isinstance(centerPt, Point):
            raise TypeError('center must be specified as a Point')

        Rectangle.__init__(self, size, size, centerPt)

    def getSize(self):
        """Return the length of a side of the square."""
        return self.getWidth()

    def setSize(self, s):
        """Set the width and height of the square to s."""
        if not isinstance(s, (int,float)):
            raise TypeError('size must be numeric')
        if s <= 0:
            raise ValueError('size must be positive')

        # TODO:  Could do freeze/unfreeze to make atomic (if not currently frozen)
        Rectangle.setWidth(self, s)
        Rectangle.setHeight(self, s)

    def setWidth(self, w):
        """Set the width and height of the square to w."""
        if not isinstance(w, (int,float)):
            raise TypeError('width must be numeric')
        if w <= 0:
            raise ValueError("width must be positive")
        self.setSize(w)

    def setHeight(self, h):
        """Set the width and height of the square to h."""
        if not isinstance(h, (int,float)):
            raise TypeError('height must be numeric')
        if h <= 0:
            raise ValueError("height must be positive")
        self.setSize(h)

class Path(Shape):
    """A path that can be drawn to a canvas."""

    def __init__(self, *points):
        """Construct a new instance of a Path.

        The path is described as a series of points that are connected in order.

        These points can be initialized by sending each individual Point
        as a separate parameter, or by sending a single parameter
        containing a sequence of Points. If no parameters are sent, the
        path initially has zero points.

        The reference point for a path is initially aligned with the first
        point of the path.
        """

        Shape.__init__(self)

        if len(points) == 1:
            try:
                points = tuple(points[0])
            except TypeError:
                pass   # original parameter might be a single Point

        for p in points:
            if not isinstance(p, Point):
                raise TypeError('non-Point specified as parameter')
        self._points = list(points)
        if len(self._points) >= 1:
            self.adjustReference(self._points[0].getX(), self._points[0].getY())
        self._final = False
        self._arrows = (False,False)

    def _getProperties(self):
        prop = Shape._getProperties(self)
        prop['points'] = tuple(self._points)
        prop['arrows'] = self._arrows
        return prop

    def finalize(self):
        """Finalize the shape.

        Once finalized, points can no longer be added, deleted, or modified.

        """
        self._final = True
        
    def addPoint(self, point, index=-1):
        """Add a new point to the Path.

        point  a Point instance
        index  designates where on the path the new point is placed
               (default at the end)

        """
        if self._final:
            raise Exception('cannot add points once finalized')
        if not isinstance(point, Point):
            raise TypeError('parameter must be a Point instance')
        if index > -1:
            self._points.insert(index, point)
        else:
            self._points.append(point)
        if len(self._points) == 1:                               # first point added
            self._reference = Point(point.getX(), point.getY())
        self._update({'points': tuple(self._points)})

    def deletePoint(self, index=-1):
        """Remove the Point at the given index.

        By default, deletes the last point.

        """
        if self._final:
            raise Exception('cannot delete points once finalized')
        if not isinstance(index, int):
            raise TypeError('index must be an integer')
        try:
            self._points.pop(index)
        except IndexError:
            raise IndexError('index out of range')
        self._update({'points': tuple(self._points)})

    def clearPoints(self):
        """Remove all points, setting this back to an empty Path."""
        if self._final:
            raise Exception('cannot clear points once finalized')
        self._points = list()
        self._update({'points': tuple(self._points)})

    def getNumberOfPoints(self):
        """Return the current number of points."""
        return len(self._points)

    def getPoint(self, index):
        """Return a copy of the Point at the given index.

        Subsequently mutating that copy has no effect on the Path.

        """
        if not isinstance(index, int):
            raise TypeError('index must be an integer')
        try:
            p = self._points[index]
        except IndexError:
            raise IndexError('index out of range')
        return Point(p.getX(), p.getY())

    def setPoint(self, point, index=-1):
        """Change the Point at the given index to a new value.

        By default, the last point is changed.

        """
        if self._final:
            raise Exception('cannot modify points once finalized')
        if not isinstance(index, int):
            raise TypeError('index must be an integer')
        if not isinstance(point, Point):
            raise TypeError('first parameter must be a Point instance')
        try:
            self._points[index] = point
        except IndexError:
            raise IndexError('index out of range')
        self._update({'points': tuple(self._points)})

    def getPoints(self):
        """Return a list of Point instances that are copies of the points on the Path."""
        return list(self._points)

    def setArrows(self, forward, reverse=False):
        """Change setting for whether arrows are drawn at beginning and end of path.

        If forward is True, will draw an arrow at the last point on the path.
        Otherwise, no such arrow is drawn.

        If reverse is True, will draw a reverse arrow eminating from
        the first point on the path; otherwise (the default), no such
        arrow is drawn.

        Note: arrows are never displayed for Polygon or ClosedSpline instances
        """
        self._arrows = (forward,reverse)
        self._update({'arrows' : self._arrows})

class Polygon(Path,FillableShape):
    """A polygon that can be drawn to a canvas."""

    def __init__(self, *points):
        """Construct a new Polygon instance.

        The polygon is described as a series of points that are connected in order.
        The last point is automatically connected back to the first to close the polygon.

        These points can be initialized by sending each individual Point
        as a separate parameter, or by sending a single parameter
        containing a sequence of Points. If no parameters are sent, the
        polygon initially has zero points.

        The reference point for a polygon is initially aligned with the
        first point of the polygon.

        """
        FillableShape.__init__(self)
        try:
            Path.__init__(self, *points)
        except TypeError:
            raise

    def _getProperties(self):    # need aspects of both parents
        prop = Path._getProperties(self)
        prop.update(FillableShape._getProperties(self))
        return prop

class Spline(Path):
    """A curved path that can be drawn to a canvas."""

    def __init__(self, *points):
        """
        Construct a new instance of a Spline.

        The spline is described as a series of points that are connected in order
        with curves.

        These points can be initialized by sending each individual Point
        as a separate parameter, or by sending a single parameter
        containing a sequence of Points. If no parameters are sent, the
        path initially has zero points.

        The reference point for a spline is initially aligned with the first
        point of the spline.

        """
        try:
            Path.__init__(self, *points)
        except TypeError:
            raise

    def _getProperties(self):
        prop = Path._getProperties(self)
        prop['smooth'] = True               # need key, but value is really irrelevant
        return prop

class ClosedSpline(Polygon):
    """A closed curve that can be drawn to a canvas."""

    def __init__(self, *points):
        """Construct a new ClosedSpline instance.

        The cuved spline is described as a series of points that are connected in order.
        The last point is automatically connected back to the first to close the spline.

        These points can be initialized by sending each individual Point
        as a separate parameter, or by sending a single parameter
        containing a sequence of Points. If no parameters are sent, the
        polygon initially has zero points.

        The reference point for a closed spline is initially aligned with the
        first point of the spline.

        """
        try:
            Polygon.__init__(self, *points)
        except TypeError:
            raise

    def _getProperties(self):
        prop = Polygon._getProperties(self)
        prop['smooth'] = True               # need key, but value is really irrelevant
        return prop

class Text(Drawable):
    """A piece of text that can be drawn to a canvas."""

    def __init__(self, message='', fontsize=12, centerPt=None):
        """
        Construct a new Text instance.

        The text color is initially black, although this can be changed by
        setColor.  The reference point for the text is initially its center.

        message   a string which is to be displayed (default empty string)
        fontsize  the font size (default 12)
        centerPt  where to locate the center of the text (default Point(0,0) )

        By default, multiline text will be left-justified, although
        this style can be changed by the setJustification method.

        """
        if not isinstance(message, basestring):
            raise TypeError('message must be a string')
        if not isinstance(fontsize, (int,float)):
            raise TypeError('fontsize must be numeric')
        if fontsize <= 0:
            raise ValueError('fontsize must be positive')
        if centerPt and not isinstance(centerPt, Point):
            raise TypeError('center must be a Point')

        Drawable.__init__(self)
        self._text = message
        self._size = fontsize
        self._color = Color('black')
        self._color._register(self, 'font color')
        if centerPt:
            self.move(centerPt.getX(), centerPt.getY())
        self._justify = 'left'

    def __deepcopy__(self, memo={}):
        temp = Drawable.__deepcopy__(self, memo)
        temp._color = self._color     # do shallow copy
        temp._color._register(temp, 'font color')
        return temp
 
    def _draw(self): pass

    def _getProperties(self):
        prop = Drawable._getProperties(self)
        prop.update( { 'message' : self._text, 'font color' : Color(self._color),
                       'font size' : self._size, 'justify' : self._justify } )
        return prop

    def setMessage(self, message):
        """Set the string to be displayed.

        message  a string

        """
        if not isinstance(message, basestring):
            raise TypeError('message must be a string')
        self._text = message
        self._update({'message': message})

    def getMessage(self):
        """Return the current string."""
        return self._text

    def setFontColor(self, color):
        """Set the color of the font.

        The parameter can be either:
             - a string with the name of the color
             - an (r,g,b) tuple
             - an existing Color instance

        """
        if self._color is not color:
            old = self._color
            if isinstance(color, Color):
                self._color = color
            else:
                try:
                    self._color = Color(color)
                except (TypeError, ValueError):
                    raise

            old._unregister(self, 'font color')
            self._color._register(self, 'font color')
            self._update({'font color': Color(self._color)})

    def getFontColor(self):
        """Return the current font color."""
        return self._color

    def setFontSize(self, fontsize):
        """Set the font size."""
        if not isinstance(fontsize, (int,float)):
            raise TypeError('fontsize must be numeric')
        if fontsize <= 0:
            raise ValueError('fontsize must be positive')

        self._size = fontsize
        self._update({'font size': self._size})

    def getFontSize(self):
        """Return the current font size."""
        return self._size

    def scale(self, factor):
        """Scale the object relative to its current reference point.

        factor      scale is multiplied by this number (must be positive)

        """
        if not isinstance(factor, (int,float)):
            raise TypeError('scaling factor must be a positive number')
        if factor <= 0:
            raise ValueError('scaling factor must be a positive number')

        Drawable.scale(self, factor)    # transform is really irrelevant, but leaving this to support TextBox type usage
        self._size *= factor
        self._update({'font size': self._size})

    def rotate(self,angle):
        """Not yet implemented."""
        raise NotImplementedError('rotating text is not yet implemented')

    def stretch(self,xFactor,yFactor,angle=0):
        """Not yet implemented."""
        raise NotImplementedError('stretching text is not yet implemented')

    def flip(self,angle=0):
        """Not yet implemented."""
        raise NotImplementedError('fliping text is not yet implemented')

    def shear(self, shear, angle=0):
        """Not yet implemented."""
        raise NotImplementedError('shearing text is not yet implemented')

    def getDimensions(self):
        """Return a (width,height) tuple measuring visual dimensions of currently displayed message."""
        return _graphicsManager.executeFunction( ('get text size', self._text, self._size) )

    def setJustification(self, style):
        """Set the justifcation style for multiline text.

        style   must be either 'left', 'right', or 'center'

        By default, text is center justified.
        """
        if not isinstance(style, basestring):
            raise TypeError('style must be a string')
        if style not in ('left', 'right', 'center'):
            raise ValueError("style must be 'left', 'right', or 'center'")
        self._justify = style
        self._update({'justify': style})



class Image(Drawable):
    """A wrapper for images that can be drawn to a canvas and manipulated."""

    def __init__(self, *args):
        """Construct a new Image instance.

        If invoked as Image(filename), the image will be constructed
        based on the contents of an underlying image file.
        gif format should be supported universally; support for
        additional image formats (e.g., jpg) will be system dependent.
        Install Pythin Image Library (PIL) for more options.

        If invoked as Image(width, height), a new image is created
        with the given dimensions, and with all pixels are initially
        Transparent.

        Once it is constructed, the virtual width and height of the
        image is fixed, and a coordinate system is used for accessing
        individual pixels of the image.

        However, the virtual image may be rendered at any size on a
        Canvas through use of methods such as scale inherited from Drawable.

        The center of the image is initially aligned with Point(0,0).
        """
        Drawable.__init__(self)

        if not 1 <= len(args) <= 2:
            raise TypeError('must either specify a filename or integer width and height')

        if len(args) == 2:
            for k in (0,1):
                if not isinstance(args[k], int):
                    msg = ('width','height')[k] + ' must be an integer'
                    raise TypeError(msg)
                if args[k] <= 0:
                    msg = ('width','height')[k] + ' must be positive'
                    raise ValueError(msg)

            self._w = args[0]
            self._h = args[1]
            self._data = _array('B', [255]) * (3 * self._w * self._h)
            self._alpha = _array('B', [0]) * ((self._w * self._h + 7)// 8)   # bitfield (all transparent)
            self._image = None
        
        if len(args) == 1:
            # TODO:  add back in base64 encoded strings for initialization? (from KAIST)
            if not isinstance(args[0], basestring):
                raise TypeError('filename must be a string')

            result = _graphicsManager.executeFunction( ('load image', args[0]) )

            if result is None:
                raise ValueError('unable to load image file: ' + args[0])
                
            self._image, self._w, self._h = result
            self._data = self._alpha = _array('B')

    def _draw(self): pass

    def _getProperties(self):
        prop = Drawable._getProperties(self)
        prop.update( { 'width' : self._w, 'height' : self._h, 'image' : self._image,
                       'data' : self._data[:], 'alpha' : self._alpha[:] } )
        return prop

    def getWidth(self):
        """Return the number of pixels per row in the original coordinate space."""
        return self._w

    def getHeight(self):
        """Return the number of pixels per column in the original coordinate space."""
        return self._h
    
    def getPixel(self, x, y):
        """Returns a copy of the color at the specified pixel."""
        if not isinstance(x, int):
            raise TypeError('x must be integral')
        if not 0 <= x < self._w:
            raise ValueError('x is invalid index')
        if not isinstance(y, int):
            raise TypeError('y must be integral')
        if not 0 <= y < self._h:
            raise ValueError('y is invalid index')
            
        
        if len(self._data) == 0:                 # lazy conversion
            self._data, self._alpha = \
                        _graphicsManager.executeFunction( ('convert image', self._image) )

        scalar = x + self._w * y
        a,b = divmod(scalar, 8)
        if self._alpha[a] & (1 << b):
            return Color(tuple(self._data[3*scalar:3*(scalar+1)]))
        else:
            return Color('transparent')

    def setPixel(self, x, y, color):
        """Set the specified pixel to the given color.

        The parameter can be either:
             - a string with the name of the color
             - an (r,g,b) tuple
             - an existing Color instance (which will be copied)

        Note: Images are intentionally implemented so that individual
        calls to setPixel are not immediately rendered.   You must call
        updatePixels() to force all changes to be rendered.

        """
        if not isinstance(x, int):
            raise TypeError('x must be integral')
        if not 0 <= x < self._w:
            raise ValueError('x is invalid index')
        if not isinstance(y, int):
            raise TypeError('y must be integral')
        if not 0 <= y < self._h:
            raise ValueError('y is invalid index')

        try:
            c = Color(color)
        except (TypeError, ValueError):
            raise

        scalar = x + self._w * y
        a,b = divmod(scalar, 8)
        if len(self._data) == 0:                 # lazy conversion
            self._data, self._alpha = \
                        _graphicsManager.executeFunction( ('convert image', self._image) )
        if c == Color('transparent'):
            self._alpha[a] &= (255-(1 << b))      # set alpha to zero
        else:
            rgb = [int(k) for k in c.getColorValue()]
            self._data[3*scalar:3*(scalar+1)] = _array('B', rgb)
            self._alpha[a] |= (1 << b)      # set alpha to one

    def updatePixels(self):
        """Re-render the image to reflect current pixel settings."""
        self._update({'data': self._data[:], 'alpha' : self._alpha[:]})


# Rendered shapes
class _RenderedDrawable(object):
    def __init__(self, chain, properties):
        self._chain = chain
        self._canvas = _graphicsManager._renderedHierarchy.getNode(chain[:1])._renderedDrawable
        self._object = None

    def putAbove(self, other):
        if other is not None:
            self._canvas._canvas.lift(self._object, other._object)
        else: # Put at bottom
            self._canvas._canvas.lower(self._object)

    def update(self, properties):
        if _debug >= 1: print('Updating _RenderedDrawable')
        pass

    def remove(self):
      self._canvas._canvas.delete(self._object)

class _RenderedShape(_RenderedDrawable):
    def __init__(self, chain, properties):
        _RenderedDrawable.__init__(self, chain, properties)
        self._width = self._transWidth = self._dash = self._borderColor = None

    def update(self, properties):
        configs = {}    # will eventually send entries to itemconfigure

        # deal with silly Tk conventions
        if isinstance(self, _RenderedFillableShape):
            colorProp = 'outline'
        else:
            colorProp = 'fill'

        if 'border width' in properties or 'transformation' in properties:
            # effective width may have changed
            w = properties.get('border width', self._width)
            if w != self._width:
                if w == 0:              # changing from nonzero to zero
                    configs[colorProp] = ''
                    self._transWidth = 0
                elif self._width == 0:  # changing from zero to nonzero!
                    configs[colorProp] = Color._getTkColor(properties.get('border color',self._borderColor))
                self._width = w

            if w != 0:     # recompute transformed width
                transform = _graphicsManager._renderedHierarchy.getNode(self._chain)._cumulativeTransformation
                self._transWidth = w * transform.scale()
                configs['width'] = self._transWidth

                if self._dash is not None and self._dash[1] != 0:
                    a = min(255, max(1, int(round(self._dash[0]*self._transWidth/self._width))))
                    b = min(255, max(1, int(round(self._dash[1]*self._transWidth/self._width))))
                    # for some reason, (a,b,a,b) tuple works better than (a,b) tuple for Tkinter
                    configs['dash'] = (a,b) * _dashMultiplier

        if 'border color' in properties:
            self._borderColor = properties['border color']
            c = Color._getTkColor(self._borderColor)
            if self._width != 0:     # border is currently rendered
                configs[colorProp] = c

        if 'dash' in properties and properties['dash'] != self._dash:
            self._dash = properties['dash']
            if self._dash[1] == 0:
                configs['dash'] = ''
            else:
                a = min(255, max(1, int(round(self._dash[0]*self._transWidth/self._width))))
                b = min(255, max(1, int(round(self._dash[1]*self._transWidth/self._width))))
                # for some reason, (a,b,a,b) tuple works better than (a,b) tuple for Tkinter
                configs['dash'] = (a,b) * _dashMultiplier

        self._canvas._canvas.itemconfigure(self._object, **configs)
        _RenderedDrawable.update(self, properties)

class _RenderedFillableShape(_RenderedShape):
    def __init__(self, chain, properties):
        _RenderedShape.__init__(self, chain, properties)
        self._fillColor = None

    def update(self, properties):
        if 'fill color' in properties:
            self._fillColor = properties['fill color']
            self._canvas._canvas.itemconfigure(self._object, fill=Color._getTkColor(self._fillColor))
        _RenderedShape.update(self, properties)

class _RenderedCircle(_RenderedFillableShape):
    def __init__(self, chain, properties):
        _RenderedFillableShape.__init__(self, chain, properties)
        transform = _graphicsManager._renderedHierarchy.getNode(chain)._cumulativeTransformation
        points = []
        for i in range(0,360,5):
            points.append(Point(1,0) ^ i)
        statement = 'self._object = self._canvas._canvas.create_polygon('
        for p in points:
            statement += str(transform.image(p).getX()) + ', ' + str(transform.image(p).getY()) + ', '
        statement += 'smooth=1)'
        exec(statement)
        _graphicsManager._objectIdRegistry[(self._canvas._canvas,self._object)] = self

        _RenderedFillableShape.update(self, properties)

    def update(self, properties):
        if 'transformation' in properties:
            transform = _graphicsManager._renderedHierarchy.getNode(self._chain)._cumulativeTransformation

            points = []
            for i in range(0,360,5):
                points.append(Point(1,0) ^ i)
            statement = 'self._canvas._canvas.coords(self._object'
            for p in points:
                statement += ', ' + str(transform.image(p).getX()) + ', ' + str(transform.image(p).getY())
            statement += ')'

            exec(statement)

        _RenderedFillableShape.update(self, properties)

class _RenderedRectangle(_RenderedFillableShape):
    def __init__(self, chain, properties):
        _RenderedFillableShape.__init__(self, chain, properties)
        transform = _graphicsManager._renderedHierarchy.getNode(self._chain)._cumulativeTransformation

        points = [Point(-.5,-.5), Point(-.5,.5), Point(.5,.5), Point(.5,-.5)]
        for i in range(4):
            points[i] = transform.image(points[i])
        self._object = self._canvas._canvas.create_polygon(points[0].get(), points[1].get(), points[2].get(), points[3].get())
        _graphicsManager._objectIdRegistry[(self._canvas._canvas,self._object)] = self
        _RenderedFillableShape.update(self, properties)

    def update(self, properties):
        if 'transformation' in properties:
            transform = _graphicsManager._renderedHierarchy.getNode(self._chain)._cumulativeTransformation
            points = [Point(-.5,-.5), Point(-.5,.5), Point(.5,.5), Point(.5,-.5)]
            for i in range(4):
                points[i] = transform.image(points[i])
            self._canvas._canvas.coords(self._object, points[0].getX(), points[0].getY(), points[1].getX(), points[1].getY(),
                                        points[2].getX(), points[2].getY(), points[3].getX(), points[3].getY())
        _RenderedFillableShape.update(self, properties)

class _RenderedPath(_RenderedShape):
    def __init__(self, chain, properties):
        _RenderedShape.__init__(self, chain, properties)
        transform = _graphicsManager._renderedHierarchy.getNode(self._chain)._cumulativeTransformation
        self._points = properties['points']

        if len(self._points) > 1:
            tkPts = [(transform.image(p).getX(),transform.image(p).getY()) for p in self._points]
        else:
            tkPts = [(0,0)] * 3
        self._object = self._canvas._canvas.create_line(tkPts)
        _graphicsManager._objectIdRegistry[(self._canvas._canvas,self._object)] = self
        _RenderedShape.update(self, properties)
        configs = {}
        if 'smooth' in properties:
            configs['smooth'] = 1

        if 'arrows' in properties:
            transform = _graphicsManager._renderedHierarchy.getNode(self._chain)._cumulativeTransformation
            w = transform.scale()*properties['border width']
            configs['arrowshape'] = str(w*8) + ' ' + str(w*10) + ' ' + str(w*3)
            pair = properties['arrows']
            if pair[0] and pair[1]:
                configs['arrow'] = 'both'
            elif pair[0]:
                configs['arrow'] = 'last'
            elif pair[1]:
                configs['arrow'] = 'first'
        if not self._points:      # make effectively invisible TK object with width 0
            configs.update( {'fill' : None, 'width' : 0} )

        if configs:
            self._canvas._canvas.itemconfigure(self._object, **configs)


    def update(self, properties):
        _RenderedShape.update(self, properties)

        configs = {}

        if 'transformation' in properties or 'points' in properties:
            wasEmpty = len(self._points) < 2
            self._points = properties.get('points', self._points)   # update if given

            if len(self._points) > 1:
                transform = _graphicsManager._renderedHierarchy.getNode(self._chain)._cumulativeTransformation
                tkCoords = []
                for p in self._points:
                    tkCoords.append(transform.image(p).getX())
                    tkCoords.append(transform.image(p).getY())
                tkCoords = tuple(tkCoords)
                if wasEmpty:   # need to explicitly (re)set border properties
                    configs['width'] = self._transWidth
                    configs['fill'] = Color._getTkColor(self._borderColor)
            else:
                tkCoords = 6 * (0,)
            self._canvas._canvas.coords(self._object,tuple(tkCoords))

        if 'transformation' in properties or 'border width' in properties:
            w = self._transWidth
            configs['arrowshape'] = str(w*8) + ' ' + str(w*10) + ' ' + str(w*3)

        if 'arrows' in properties:
            pair = properties['arrows']
            if pair[0] and pair[1]:
                configs['arrow'] = 'both'
            elif pair[0]:
                configs['arrow'] = 'last'
            elif pair[1]:
                configs['arrow'] = 'first'
            else:
                configs['arrow'] = 'none'

        if not self._points:      # make effectively invisible TK object with width 0
            configs.update( {'fill' : None, 'width' : 0} )

        if configs:
            self._canvas._canvas.itemconfigure(self._object, **configs)

class _RenderedPolygon(_RenderedFillableShape):
    def __init__(self, chain, properties):
        _RenderedFillableShape.__init__(self, chain, properties)
        transform = _graphicsManager._renderedHierarchy.getNode(self._chain)._cumulativeTransformation
        self._points = properties['points']

        if len(self._points) > 1:
            tkPts = [(transform.image(p).getX(),transform.image(p).getY()) for p in self._points]
        else:
            tkPts = [(0,0)] * 3
        self._object = self._canvas._canvas.create_polygon(tkPts)
        _graphicsManager._objectIdRegistry[(self._canvas._canvas,self._object)] = self
        if 'smooth' in properties:
            self._canvas._canvas.itemconfigure(self._object, smooth=1)
        _RenderedFillableShape.update(self, properties)
        if not self._points:      # make effectively invisible TK object with width 0
            self._canvas._canvas.itemconfigure(self._object, fill=None, width=0)

    def update(self, properties):
        _RenderedFillableShape.update(self, properties)
        configs = {}

        if 'transformation' in properties or 'points' in properties:
            wasEmpty = len(self._points)  < 2
            self._points = properties.get('points', self._points)   # update if given

            if len(self._points) > 1:
                transform = _graphicsManager._renderedHierarchy.getNode(self._chain)._cumulativeTransformation
                tkCoords = []
                for p in self._points:
                    tkCoords.append(transform.image(p).getX())
                    tkCoords.append(transform.image(p).getY())
                tkCoords = tuple(tkCoords)
                if wasEmpty:   # need to explicitly (re)set border properties
                    configs['width'] = self._transWidth
                    configs['outline'] = Color._getTkColor(self._borderColor)
                    configs['fill'] = Color._getTkColor(self._fillColor)
            else:
                tkCoords = 6 * (0,)
            self._canvas._canvas.coords(self._object,tuple(tkCoords))

        if not self._points:      # make effectively invisible TK object with width 0
            configs.update( {'fill' : None, 'width' : 0} )

        if configs:
            self._canvas._canvas.itemconfigure(self._object, **configs)

class _RenderedText(_RenderedDrawable):

    normalFactor = 1.0    # re-configured at startup so that 12pt font has approximate height 16-pixels (96 PPI)
    
    def __init__(self, chain, properties):
        _RenderedDrawable.__init__(self, chain, properties)
        transform = _graphicsManager._renderedHierarchy.getNode(chain)._cumulativeTransformation
        parentTransform = _graphicsManager._renderedHierarchy.getNode(chain[:-1])._cumulativeTransformation
        parentScale = parentTransform.scale()
        if not transform.scaleAndTranslate() and parentScale > 0:
            raise GraphicsError('text cannot be rotated or sheared unless Python Image Library is installed', True)
        center = transform.image(Point(0.,0.))
        self._renderedSize = properties['font size']
        actualSize = int(round(parentScale * self._renderedSize * _RenderedText.normalFactor))
        self._object = self._canvas._canvas.create_text(center.get(), text=properties['message'],
                                                        anchor='center', justify=properties['justify'],
                                                        fill=Color._getTkColor(properties['font color']),
                                                        font=('Helvetica', actualSize, 'normal') )
        _graphicsManager._objectIdRegistry[(self._canvas._canvas,self._object)] = self

        _RenderedDrawable.update(self, properties)

    def update(self, properties):
        if 'message' in properties:
            self._canvas._canvas.itemconfigure(self._object, text=properties['message'])

        if 'font color' in properties:
            self._canvas._canvas.itemconfigure(self._object, fill=Color._getTkColor(properties['font color']))
            
        if 'justify' in properties:
            self._canvas._canvas.itemconfigure(self._object, justify=properties['justify'])
            
        if 'font size' in properties:
            self._renderedSize = properties['font size']
            # will handle the actual resizeing of tkinter in a moment...

        if 'font size' in properties or 'transformation' in properties:
            # determine effective size
            parentTransform = _graphicsManager._renderedHierarchy.getNode(self._chain[:-1])._cumulativeTransformation
            parentScale = parentTransform.scale()
            if parentScale < 0:
#                raise GraphicsError('text cannot be reflected unless Python Image Library is installed', True)
                raise GraphicsError('text cannot be reflected', True)
            actualSize = int(round(parentScale * self._renderedSize * _RenderedText.normalFactor))
            self._canvas._canvas.itemconfigure(self._object, font=('Helvetica', actualSize, 'normal'))

        if 'transformation' in properties:
            # consider translation of text center
            transform = _graphicsManager._renderedHierarchy.getNode(self._chain)._cumulativeTransformation
            if not transform.scaleAndTranslate():
#                raise GraphicsError('text cannot be rotated or sheared unless Python Image Library is installed', True)
                raise GraphicsError('text cannot be rotated or sheared', True)
            center = transform.image(Point(0.,0.))
            self._canvas._canvas.coords(self._object, center.getX(), center.getY())


        _RenderedDrawable.update(self, properties)

class _RenderedImage(_RenderedDrawable):
    # need to make sure that this instance buffers the most recently used
    # image, transform, and (data,alpha) arrays.
    
    def __init__(self, chain, properties):
        _RenderedDrawable.__init__(self, chain, properties)

        self._w = properties['width']            # needed for _buildImage
        self._h = properties['height']
        self._lastData = self._lastAlpha = None

        transform = _graphicsManager._renderedHierarchy.getNode(chain)._cumulativeTransformation
        center = transform.image(Point(0.,0.))

        if properties['data'] or not transform.translateOnly():
            # will need to construct image manually
            if properties['data']:
                data,alpha = properties['data'], properties['alpha']
            else:
                data,alpha = _convertImage(properties['image'])
            self._lastData, self._lastAlpha = data,alpha
            img = self._buildImage(data, alpha, transform)
        else:
            img = properties['image']

        self._lastCumulative = transform    # used to recognize translationOnly updates
        self._lastImage = img               # keep reference to avoid garbage collection
        self._object = self._canvas._canvas.create_image(center.get(), image=img, anchor='center')
        _graphicsManager._objectIdRegistry[(self._canvas._canvas,self._object)] = self
        _RenderedDrawable.update(self, properties)

    def update(self, properties):
        mustRebuild = 'data' in properties
        if mustRebuild or 'transformation' in properties:
            transform = _graphicsManager._renderedHierarchy.getNode(self._chain)._cumulativeTransformation
            delta = transform * self._lastCumulative.inv()
            mustRebuild = mustRebuild or not delta.translateOnly()
            self._lastCumulative = transform

            if not mustRebuild:
                # can get away with simple translation with existing image
                center = transform.image(Point(0.,0.))
                self._canvas._canvas.coords(self._object, center.getX(), center.getY())

        if mustRebuild:
            if 'data' in properties:
                data,alpha = properties['data'], properties['alpha']
            elif self._lastData is not None:
                data,alpha = self._lastData, self._lastAlpha
            else:
                data,alpha = _convertImage(self._lastImage)
            self._lastData, self._lastAlpha = data,alpha
            self._image = self._buildImage(data, alpha, transform)
            center = transform.image(Point(0,0))
            self._canvas._canvas.itemconfigure(self._object, image=self._image)

        _RenderedDrawable.update(self, properties)

    def _buildImage(self, data, alpha, transform):
        """Returns a new PhotoImage instance based on the transformed low-level data arrays."""
        # TODO: find ways to batch so that there are less individual calls to img.put
        minX = maxX = minY = maxY = None
        for x,y in ( (self._w,0), (0,self._h), (self._w,self._h), (0,0)):   # do origin last!
            p = transform.image(Point(x,y))
            if minX is None or minX > p.getX():
                minX = p.getX()
            if maxX is None or maxX < p.getX():
                maxX = p.getX()
            if minY is None or minY > p.getY():
                minY = p.getY()
            if maxY is None or maxY < p.getY():
                maxY = p.getY()
        offset = Point(p.getX()-minX, p.getY()-minY)
        rW = int(round(maxX-minX))
        rH = int(round(maxY-minY))
        img = _Tkinter.PhotoImage(width=rW, height=rH)
        img.blank()   # TODO: is this necessary for newly constructed image?  

        for y in range(rH):
            for x in range(rW):
                result = transform.inv().image(Point(x+minX,y+minY))
                # no anti-aliasing in this version
                vx = int(round(result.getX()))      
                vy = int(round(result.getY()))
                if 0 <= vx < self._w and 0 <= vy < self._h:
                    a,b = divmod(self._w * vy + vx, 8)
                    if alpha[a] & (1 << b):
                        color = '#%02x%02x%02x'%tuple(data[3*(vx+self._w*vy):3*(1+vx+self._w*vy)])
                        img.put(data=color, to=(x,y))
        return img

# Library initialization and shutdown
def _initLibrary():
    global _tkroot
    try:
        _tkroot = _Tkinter.Tk()
    except KeyboardInterrupt:
        raise
    except:
        raise Exception('unable to start Tkinter on your system')
        _graphicsManager._state = 'Failed'
    _tkroot.withdraw()
    actual = _getTextSize('X', 36)[1]
    _RenderedText.normalFactor *= 48.0 / actual  # this normalizes so that 36-pt font has 48-pixel height (96 PPI)

def _startCommandThread():
    _initLibrary()
    while _graphicsManager._state == 'Running':
        _graphicsManager.processCommands()
        _graphicsManager.processEvents()
        _tkroot.update()
        _time.sleep(.01)

def _stopCommandThread():
    while len(_graphicsManager._openCanvases) > 0:
        _time.sleep(.25)
    _graphicsManager._state = 'Stopped'
    _time.sleep(.25)
    
def _exitMainThread():
    # Main loop will return when all open canvases closed
    if _graphicsManager._handlingEvents == 'No':
        _graphicsManager._handlingEvents = 'Yes'
    if len(_graphicsManager._openCanvases) > 0:
        print('Close canvas windows to end program.')
        _graphicsManager.mainLoop(None, True)
    
def startEventHandling():
    """
    Blocks the main thread and enters event-handling mode.

    This can be counteracted by a later call to stopEventHandling().

    Note: This should not be called if using native threading.
    """
    if not _nativeThreading:
      if _graphicsManager._handlingEvents == 'No':
          _graphicsManager._handlingEvents = 'Yes'
      _graphicsManager.mainLoop()
    
def stopEventHandling():
    """
    Counteracts an earlier call to startEventHandling().
    """
    if not _nativeThreading:
      if _graphicsManager._handlingEvents == 'Yes':
          _graphicsManager._handlingEvents = 'No'

_graphicsManager = _GraphicsManager()


# Utility for Text.  This is used once at startup to normalize measure
# and subsequently to support calls to Text.getDimensions()
# it presumes that the lock is already held for the graphics thread
def _getTextSize(message, fontsize):
    tkWin = _Tkinter.Toplevel()
    canvas = _Tkinter.Canvas(tkWin)
    size = int(round(fontsize * _RenderedText.normalFactor))
    i = canvas.create_text(0, 0, text=message, font=('Helvetica', size, 'normal') )
    bbox = canvas.bbox(i)
    canvas.delete(i)
    tkWin.withdraw()
    return (bbox[2]-bbox[0],bbox[3]-bbox[1])


# Utility for Image Processing
def _convertImage(img):
    """Takes a PhotoImage instance, and produces array pixmap representation.

    Formally, returns pair of arrays.

    First is array of bytes describing the colors (in row-major
    order), and a second array that is used as a bitfield for
    transparency representation.
    """
    w = img.width()
    h = img.height()
    a = _array('B', [0]) * (3*w*h)
    t = _array('B', [255]) * ((w*h+7)//8)     # all True, for lack of better idea
    for x in range(w):
        for y in range(h):
            color = img.get(x,y)
            base = 3 * (y*w + x)
            a[base:base+3] = _array('B', [int(v) for v in color.split()])

            # appears to be no way to differentiate between black and transparent in this context
            # If we knew it was transparent, the following is the proper code.
#            if color == '0 0 0':          
#                u,v = divmod(y*w+x,8)
#                t[u] &= (255 - (1 << v))   # make transparent
    return (a,t)
    

# TODO timer, etc.
