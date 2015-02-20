# -*- coding: utf-8 -*-
"""
Created on Fri Jan 23 10:07:42 2015

@author: aseth
"""
import copy
import networkx as nx
import math
from scipy.optimize import fsolve


class WaterNetworkModel(object):

    """
    The base water network model class.
    """
    def __init__(self):
        """
        Example
        ---------
        >>> wn = WaterNetworkModel()
        
        """

        # Network name
        self.name = None

        # Initialize Network size parameters
        self._num_nodes = 0
        self._num_links = 0
        self._num_junctions = 0
        self._num_reservoirs = 0
        self._num_tanks = 0
        self._num_pipes = 0
        self._num_pumps = 0
        self._num_valves = 0

        # Initialize node an link lists
        # Dictionary of node or link objects indexed by their names
        self._nodes = {}
        self._links = {}

        # Initialize pattern and curve dictionaries
        # Dictionary of pattern or curves indexed by their names
        self._patterns = {}
        self._curves = {}

        # Initialize Options dictionaries
        self.time_options = {}
        self.options = {}

        # Time controls are saved as a dictionary as follows:
        # {'Link name': {'open_times': [1, 5, ...], 'closed_times': [3, 7, ...]}},
        # where times are in minutes
        self.time_controls = {}

        # NetworkX Graph to store the pipe connectivity and node coordinates
        # SOULD THIS BE PRIVATE ??????
        self.graph = nx.MultiDiGraph(data=None)


    def copy(self):
        """
        Copy a water network object
        Return
        ------
        A copy of the water network

        Example
        ------
        >>> wn = WaterNetwork()
        >>> wn2 = wn.copy()
        """
        return copy.deepcopy(self)

    def get_node(self, name):
        """
        Returns node object of a provided name

        Parameter
        --------
        name : string
            name of the node
        """
        return self._nodes[name]

    def get_link(self, name):
        """
        Returns link object of a provided name

        Parameter
        --------
        name : string
            name of the link
        """
        return self._links[name]

    def get_curve(self, name):
        """
        Returns curve object of a provided name

        Parameter
        --------
        name : string
            name of the curve
        """
        return self._curves[name]

    def get_pattern(self, name):
        """
        Returns pattern object of a provided name

        Parameter
        --------
        name : string
            name of the pattern
        """
        return self._patterns[name]

    def add_junction(self, name, base_demand=None, demand_pattern_name=None, elevation=None):
        """
        Add a junction to the network.
        Parameters
        -------
        name : string
            Name of the junction.

        Optional Parameters
        -------
        base_demand : float
            Base demand at the junction.
            Internal units must be cubic meters per second (m^3/s).
        demand_pattern_name : string
            Name of the demand pattern.
        elevation : float
            Elevation of the junction.
            Internal units must be meters (m).

        """
        junction = Junction(name, base_demand, demand_pattern_name, elevation)
        self._nodes[name] = junction
        self._num_nodes += 1
        self._num_junctions += 1

    def add_tank(self, name, elevation=None, init_level=None,
                 min_level=None, max_level=None, diameter=None,
                 min_vol=None, vol_curve=None):
        """
        Method to add tank to a water network object.

        Parameters
        ------
        name : string
            Name of the tank.

        Optional Parameters
        -------
        elevation : float
            Elevation at the Tank.
            Internal units must be meters (m).
        init_level : float
            Initial tank level.
            Internal units must be meters (m).
        min_level : float
            Minimum tank level.
            Internal units must be meters (m)
        max_level : float
            Maximum tank level.
            Internal units must be meters (m)
        diameter : float
            Tank diameter.
            Internal units must be meters (m)
        min_vol : float
            Minimum tank volume.
            Internal units must be cubic meters (m^3)
        vol_curve_name : string
            Name of the tank volume curve.
        """
        tank = Tank(name, elevation, init_level,
                 min_level, max_level, diameter,
                 min_vol, vol_curve)
        self._nodes[name] = tank
        self._num_nodes += 1
        self._num_tanks += 1


    def add_reservoir(self, name, base_head=None, head_pattern_name=None):
        """
        Method to add reservoir to a water network object.

        Parameters
        ------
        name : string
            Name of the reservoir.

        Optional Parameters
        -------
        base_head : float
            Base head at the reservoir.
            Internal units must be meters (m).
        head_pattern_name : string
            Name of the head pattern.
        """
        reservoir = Reservoir(name, base_head, head_pattern_name)
        self._nodes[name] = reservoir
        self._num_nodes += 1
        self._num_reservoirs += 1

    def add_pipe(self, name, start_node_name, end_node_name, length=None,
                 diameter=None, roughness=None, minor_loss=None, status=None):
        """
        Method to add pipe to a water network object.

        Parameters
        ----------
        name : string
            Name of the pipe
        start_node_name : string
             Name of the start node
        end_node_name : string
             Name of the end node

        Optional Parameters
        -----------
        length : float
            Length of the pipe.
            Internal units must be meters (m)
        diameter : float
            Diameter of the pipe.
            Internal units must be meters (m)
        roughness : float
            Pipe roughness coefficient
        minor_loss : float
            Pipe minor loss coefficient
        status : string
            Pipe status. Options are 'Open', 'Closed', and 'CV'
        """
        pipe = Pipe(name, start_node_name, end_node_name, length,
                    diameter, roughness, minor_loss, status)
        self._links[name] = pipe
        self._num_links += 1
        self._num_pipes += 1

    def add_pump(self, name, start_node_name, end_node_name, curve_name=None):
        """
        Method to add pump to a water network object.

        Parameters
        ----------
        name : string
            Name of the pump
        start_node_name : string
             Name of the start node
        end_node_name : string
             Name of the end node

        Optional Parameters
        ----------
        curve_name : string
            Name of the pump curve.
        """
        pump = Pump(name, start_node_name, end_node_name, curve_name)
        self._links[name] = pump
        self._num_links += 1
        self._num_pumps += 1

    def add_valve(self, name, start_node_name, end_node_name,
                 diameter=None, valve_type=None, minor_loss=None, setting=None):
        """
        Method to add valve to a water network object.

        Parameters
        ----------
        name : string
            Name of the valve
        start_node_name : string
             Name of the start node
        end_node_name : string
             Name of the end node

        Optional Parameters
        ----------
        diameter : float
            Diameter of the valve.
            Internal units must be meters (m)
        valve_type : string
            Type of valve. Options are 'PRV', etc
        minor_loss : float
            Pipe minor loss coefficient
        setting : string
            Valve status. Options are 'Open', 'Closed', etc
        """
        valve = Valve(name, start_node_name, end_node_name,
                      diameter, valve_type, minor_loss, setting)
        self._links[name] = valve
        self._num_links += 1
        self._num_valves += 1

    def add_pattern(self, name, pattern_list):
        """
        Method to add pattern to a water network object.

        Parameters
        ---------
        name : string
            name of the pattern
        pattern_list : list of floats
            A list of floats that make up the pattern.
        """
        self._patterns[name] = pattern_list

    def add_curve(self, name, curve_type, xy_tuples_list):
        """
        Method to add a curve to a water network object.

        Parameters
        ---------
        name : string
            Name of the curve
        curve_type : string
            Type of curve. Options are HEAD, EFFICIENCY, VOLUME, HEADLOSS
        xy_tuples_list : list of tuples
            List of X-Y coordinate tuples on the curve.
        """
        curve = Curve(name, curve_type, xy_tuples_list)
        self._curves[name] = curve

    def add_time_parameter(self, name, value):
        """
        Method to add a time parameter to a water network object.

        Parameters
        -------
        name : string
            Name of the time option.
        value:
            Value of the time option. Must be in minutes.

        Example
        -------
        START CLOCKTIME = 6 PM can be set using
        >>> wn.add_time_parameter('START CLOCKTIME', 1080)
        """
        self.time_options[name.upper()] = value

    def add_option(self, name, value):
        """
        Method to add a options to a water network object.

        Parameters
        -------
        name : string
            Name of the option.
        value:
            Value of the option.
        """
        self.options[name.upper()] = value

    def query_node_attribute(self, attribute, operation, value):
        """ Query node attributes, for example get all nodes with elevation <= threshold

        Parameters
        ----------
        attribute: string
            Node attribute

        operation: np option
            options = np.greater, np.greater_equal, np.less, np.less_equal, np.equal, np.not_equal

        value: scalar
            threshold

        Returns
        -------
        nodes : dictionary of nodes
            dictionary of node names to node objects satisfying operation threshold
        """
        node_attribute_dict = {}
        for name, node in self._nodes.iteritems():
            try:
                node_attribute = getattr(node, attribute)
                if operation(node_attribute, value):
                    node_attribute_dict[name] = node_attribute
            except AttributeError:
                pass
        return node_attribute_dict

    def query_link_attribute(self, attribute, operation, value):
        """ Query link attributes, for example get all pipe diameters > threshold

        Parameters
        ----------
        attribute: string
            link attribute

        operation: np option
            options = np.greater, np.greater_equal, np.less, np.less_equal, np.equal, np.not_equal

        value: scalar
            threshold

        Return
        -------
        links : dictionary of links
            dictionary of link names to link objects satisfying operation threshold
        """
        link_attribute_dict = {}
        for name, link in self._links.iteritems():
            try:
                link_attribute = getattr(link, attribute)
                if operation(link_attribute, value):
                    link_attribute_dict[name] = link_attribute
            except AttributeError:
                pass
        return link_attribute_dict


    def add_time_control(self, link, open_times=[], closed_times=[]):
        """
        Add time controls to the network.

        Parameter
        -------
        link : string
            Name of the link
        open_times : list of integers
            List of times (in minutes) when the link is opened
        closed_times : list of integers
            List of times (in minutes) when the link is closed

        """
        if link not in self.time_controls:
            self.time_controls[link] = {'open_times': [i for i in open_times], 'closed_times': [i for i in closed_times]}
        else:
            self.time_controls[link]['open_times'] += open_times
            self.time_controls[link]['closed_times'] += closed_times

    def nodes(self):
        """
        A generator to iterate over all nodes

        Return:
        node_name, node
        """
        for node_name, node in self._nodes.iteritems():
            yield node_name, node

    def links(self):
        """
        A generator to iterate over all links

        Return:
        link_name, link
        """
        for link_name, link in self._links.iteritems():
            yield link_name, link

    def Curves(self):
        """
        A generator to iterate over all curves

        Return:
        curve_name, curve
        """
        for curve_name, curve in self._curves.iteritems():
            yield curve_name, curve

    def get_all_nodes_copy(self):
        """
        Return a copy of the dictionary with all nodes.

        Parameters
        -------

        Return
        -------
        node : dictionary
            Node name to node.
        """
        return copy.deepcopy(self._nodes)

    def get_all_links_copy(self):
        """
        Return a copy of the dictionary with all nodes.

        Parameters
        -------

        Return
        -------
        node : dictionary
            Node name to node.
        """
        return copy.deepcopy(self._links)

    def get_pump_coefficients(self, pump_name):
        """
        Returns the A, B, C coefficients for a 1-point or a 3-point pump curve.
        Coefficient can only be calculated for pump curves.

        For a single point curve the coefficients are generated according to the following equation:

        A = 4/3 * H_1
        B = 1/3 * H_1/Q_1^2
        C = 2

        For a three point curve the coefficients are generated according to the following equation:
             When the first point is a zero flow: (All INP files we have come across)

             A = H_1
             C = ln((H_1 - H_2)/(H_1 - H_3))/ln(Q_2/Q_3)
             B = (H_1 - H_2)/Q_2^C

             When the first point is not zero, numpy fsolve is called to solve the following system of
             equation:

             H_1 = A - B*Q_1^C
             H_2 = A - B*Q_2^C
             H_3 = A - B*Q_3^C

        Multi point curves are currently not supported

        Parameters
        -------
        pump_name : string
            Name of the pump

        Return
        -------
        Tuple of pump curve coefficient (A, B, C). All floats.
        """
        pump = self._links[pump_name]
        curve = self._curves[pump.curve_name]

        assert(isinstance(pump, Pump)), pump_name + " is not defined as a pump type. "

        # 1-Point curve
        if curve.num_points == 1:
            H_1 = curve.points[0][1]
            Q_1 = curve.points[0][0]
            A = (4.0/3.0)*H_1
            B = (1.0/3.0)*(H_1/(Q_1**2))
            C = 2
        # 3-Point curve
        elif curve.num_points == 3:
            Q_1 = curve.points[0][0]
            H_1 = curve.points[0][1]
            Q_2 = curve.points[1][0]
            H_2 = curve.points[1][1]
            Q_3 = curve.points[2][0]
            H_3 = curve.points[2][1]

            # When the first points is at zero flow
            #if Q_1 == 0.0:
            if False:
                A = H_1
                C = math.log((H_1 - H_2)/(H_1 - H_3))/math.log(Q_2/Q_3)
                B = (H_1 - H_2)/(Q_2**C)
            else:
                def curve_fit(x):
                    eq_array = [H_1 - x[0] + x[1]*Q_1**x[2],
                                H_2 - x[0] + x[1]*Q_2**x[2],
                                H_3 - x[0] + x[1]*Q_3**x[2]]
                    return eq_array
                coeff = fsolve(curve_fit, [200, 1e-3, 1.5])
                A = coeff[0]
                B = coeff[1]
                C = coeff[2]

        # Multi-point curve
        else:
            raise RuntimeError("Coefficient for Multipoint pump curves cannot be generated. ")

        return (A, B, C)


class Node(object):
    """
    The base node class.
    """
    def __init__(self, name):
        """
        Parameters
        -----------
        name : string
            Name of the node
        node_type : string
            Type of the node. Options are 'Junction', 'Tank', or 'Reservoir'

        Example
        ---------
        >>> node2 = Node('North Lake','Reservoir')
        """
        self._name = name

    def __str__(self):
        """
        Returns the name of the node when printing to a stream.
        """
        return self._name


class Link(object):
    """
    The base link class.
    """
    def __init__(self, link_name, start_node_name, end_node_name):
        """
        Parameters
        ----------
        link_name : string
            Name of the link
        link_type : string
            Type of the link. Options are 'Pipe', 'Valve', or 'Pump'
        start_node_name : string
             Name of the start node
        end_node_name : string
             Name of the end node

        Example
        ---------
        >>> link1 = Link('Pipe 1','Pipe', 'Node 153', 'Node 159')
        """
        self._link_name = link_name
        self._start_node_name = start_node_name
        self._end_node_name = end_node_name

    def __str__(self):
        """
        Returns the name of the link when printing to a stream.
        """
        return self._link_name

    def start_node(self):
        """
        Returns name of start node
        """
        return self._start_node_name

    def end_node(self):
        """
        Returns name of end node
        """
        return self._end_node_name

class Junction(Node):
    """
    Junction class that is inherited from Node
    """
    def __init__(self, name, base_demand=None, demand_pattern_name=None, elevation=None):
        """
        Parameters
        ------
        name : string
            Name of the junction.

        Optional Parameters
        -------
        base_demand : float
            Base demand at the junction.
            Internal units must be cubic meters per second (m^3/s).
        demand_pattern_name : string
            Name of the demand pattern.
        elevation : float
            Elevation of the junction.
            Internal units must be meters (m).
        """
        Node.__init__(self, name)
        self.base_demand = base_demand
        self.demand_pattern_name = demand_pattern_name
        self.elevation = elevation

    def copy(self):
        """
        Copy a junction object

        Return
        ------
        A copy of the junction.

        Example
        ------
        >>> junction1 = Junction('Node 1')
        >>>
        """
        return copy.deepcopy(self)

class Reservoir(Node):
    """
    Reservoir class that is inherited from Node
    """
    def __init__(self, name, base_head=None, head_pattern_name=None):
        """
        Parameters
        ------
        name : string
            Name of the reservoir.

        Optional Parameters
        -------
        base_head : float
            Base head at the reservoir.
            Internal units must be meters (m).
        head_pattern_name : string
            Name of the head pattern.
        """
        Node.__init__(self, name)
        self.base_head = base_head
        self.head_pattern_name = head_pattern_name

class Tank(Node):
    """
    Tank class that is inherited from Node
    """
    def __init__(self, name, elevation=None, init_level=None,
                 min_level=None, max_level=None, diameter=None,
                 min_vol=None, vol_curve=None):
        """
        Parameters
        ------
        name : string
            Name of the tank.

        Optional Parameters
        -------
        elevation : float
            Elevation at the Tank.
            Internal units must be meters (m).
        init_level : float
            Initial tank level.
            Internal units must be meters (m).
        min_level : float
            Minimum tank level.
            Internal units must be meters (m)
        max_level : float
            Maximum tank level.
            Internal units must be meters (m)
        diameter : float
            Tank diameter.
            Internal units must be meters (m)
        min_vol : float
            Minimum tank volume.
            Internal units must be cubic meters (m^3)
        vol_curve : string
            Name of the tank volume curve.
        """
        Node.__init__(self, name)
        self.elevation = elevation
        self.init_level = init_level
        self.min_level = min_level
        self.max_level = max_level
        self.diameter = diameter
        self.min_vol = min_vol
        self.vol_curve = vol_curve

class Pipe(Link):
    """
    Pipe class that is inherited from Link
    """
    def __init__(self, name, start_node_name, end_node_name, length=None,
                 diameter=None, roughness=None, minor_loss=None, status=None):
        """
        Parameters
        ----------
        name : string
            Name of the pipe
        start_node_name : string
             Name of the start node
        end_node_name : string
             Name of the end node

        Optional Parameters
        -----------
        length : float
            Length of the pipe.
            Internal units must be meters (m)
        diameter : float
            Diameter of the pipe.
            Internal units must be meters (m)
        roughness : float
            Pipe roughness coefficient
        minor_loss : float
            Pipe minor loss coefficient
        status : string
            Pipe status. Options are 'Open', 'Closed', and 'CV'
        """
        Link.__init__(self, name, start_node_name, end_node_name)
        self.length = length
        self.diameter = diameter
        self.roughness = roughness
        self.minor_loss = minor_loss
        self.status = status



class Pump(Link):
    """
    Pump class that is inherited from Link
    """
    def __init__(self, name, start_node_name, end_node_name, curve_name):
        """
        Parameters
        ----------
        name : string
            Name of the pump
        start_node_name : string
             Name of the start node
        end_node_name : string
             Name of the end node

        Optional Parameters
        ----------
        curve_name : string
            Name of the pump curve.
        """
        Link.__init__(self, name, start_node_name, end_node_name)
        self.curve_name = curve_name

class Valve(Link):
    """
    Valve class that is inherited from Link
    """
    def __init__(self, name, start_node_name, end_node_name,
                 diameter=None, valve_type=None, minor_loss=None, setting=None):
        """
        Parameters
        ----------
        name : string
            Name of the valve
        start_node_name : string
             Name of the start node
        end_node_name : string
             Name of the end node

        Optional Parameters
        ----------
        diameter : float
            Diameter of the valve.
            Internal units must be meters (m)
        valve_type : float
            Type of valve. Options are 'PRV', etc
        minor_loss : float
            Pipe minor loss coefficient
        setting : string
            Valve status. Options are 'Open', 'Closed', etc
        """
        Link.__init__(self, name, start_node_name, end_node_name)
        self.diameter = diameter
        self.valve_type = valve_type
        self.minor_loss = minor_loss
        self.setting = setting

class Curve(object):
    """
    Curve class.
    """
    def __init__(self, name, curve_type, points):
        """
        Parameters
        -------
        name : string
             Name of the curve
        curve_type :
             Type of curve. Options are Volume, Pump, Efficiency, Headloss.
        points :
             List of tuples with X-Y points.
        """
        self.name = name
        self.curve_type = curve_type
        self.points = points
        self.num_points = len(points)






