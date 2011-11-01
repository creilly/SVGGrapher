from lxml import etree
from sympy import sympify, lambdify, diff, Symbol, cos, sin
import numpy
from sympy.utilities.lambdify import lambdify

svg_attrs = dict( 
                 version = "1.1",
                 baseProfile = "full",
                 xmlns = "http://www.w3.org/2000/svg"
                 )

class Point:
    def __init__( self, x, y ):
        self.x = x
        self.y = y

class SvgElement( etree.ElementBase ):

    @staticmethod
    def length( distance, units = 'px' ):
        return str( distance ) + units

class circle( SvgElement ):

    @property
    def center( self ):
        if not hasattr( self, '_center' ):
            self._center = None
        return self._center

    @center.setter
    def center( self, center ):
        self.attrib['cx'] = self.length( center.x )
        self.attrib['cy'] = self.length( center.y )
        self._center = center

    @property
    def radius( self ):
        if not hasattr( self, '_radius' ):
            self._radius = None
        return self._radius

    @radius.setter
    def radius( self, radius ):
        self.attrib['r'] = self.length( radius )
        self._radius = radius

class Curve:
    t = Symbol( 't' )
    s = Symbol( 's' )
    def __init__( self, f, g, span, delta = None ):
        self.f = f
        self.g = g
        self.min, self.max = ( min( span ), max( span ) )
        self.delta = delta if delta else ( ( self.max - self.min ) / float( 10 ) )
        self.calculate_path()

    def calculate_path( self ):

        f, g, t, dt, s = ( self.f, self.g, self.t, self.delta, self.s )
        der_f, der_g = [ diff( coord, t ) for coord in f, g ]
        tanf, tang = [lambdify( ( t, s ), coord + der * s, numpy ) for coord, der in ( ( f, der_f ), ( g, der_g ) )]

        coords = lambdify( t, ( f, g ), numpy )
        print der_f.subs( t, t + dt )
        get_control_param = lambdify( t,
                                      ( g - g.subs( t, t + dt ) ) / ( der_g.subs( t, t + dt ) - der_g ),
                                      numpy )
        def control_coords( time ):
            control_param = get_control_param( time )
            return ( tangent( time, control_param ) for tangent in ( tanf, tang ) )

        x_o, y_o = coords( self.min )
        path = 'M%f, %f' % ( x_o, y_o )

        def append_curve( path, point, control_point ):
            return '%s Q%f, %f %f, %f' % ( path, point.x, point.y, control_point.x, control_point.y )

        for time in numpy.arange( self.min + self.delta, self.max - self.delta, self.delta ):
            x, y = coords( time )
            x_c, y_c = control_coords( time )
            path = append_curve( path, Point( x, y ), Point( x_c, y_c ) )

        x_f, y_f = coords( self.max )
        path = '%s T%f, %f' % ( path, x_f, y_f )

        self.path = path

    @property
    def to_d( self ):
        return self.path

class path( SvgElement ):
    @property
    def curve( self ):
        if not hasattr( self, '_curve' ):
            self._curve = None
        return curve

    @curve.setter
    def curve( self, curve ):
        self._curve = curve
        self.attrib['d'] = curve.to_d

doc = etree.Element( 'svg', svg_attrs )

c = circle()
c.center = Point( 10, 10 )
c.radius = 5
doc.append( c )

t = Symbol( 't' )
curve = Curve( t, t ** 2, ( 0.0, 20.0 ) )
p = path()
p.attrib['fill'] = 'none'
p.attrib['stroke'] = 'red'
p.attrib['stroke-width'] = '5px'
p.curve = curve
doc.append( p )

print etree.tostring( doc, pretty_print = True )
