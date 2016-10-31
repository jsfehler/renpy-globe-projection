init -1500 python:
    from __future__ import division
    
    from itertools import product
    import math

    import pygame

    cos = math.cos
    hypot = math.hypot

    # Functions called by the bars on the screen
    def alter_area(i):
        g.sphere_area = i
        g.scales= list(g.generate_transforms(g.idle))
        g.c_scales = list(g.generate_transforms(g.selected))

    
    def alter_point_distance(i):
        b.point_distance = (i, i)
        g.point_distance = (i, i)
    
    def get_points(world, width=0, height=0):
        """Scan world to get coordinates and make BasicPoints for 
        the displayables.
        
        Args:
            world (str): Single string that's multiplied by the width and height to create a 2D map.
            width (int):
            height (int):
        
        Yields:
            BasicPoint
        """
        for y, x in product(range(height), range(width)):
            location = (width * y) + x
            if world[location] == "1":
                yield BasicPoint(x, y)

    
    class BasicPoint(object):
        __slots__ = ['x', 'y', 'c', 'dist', 'dx', 'dy', 'x0', 'y0', 'mx', 'my']
    
        def __init__(self, x, y, c=False, dist=0, dx=0, dy=0):
            self.x = x
            self.y = y
            self.c = c
            self.dist = dist
            self.dx = dx
            self.dy = dy

            self.x0 = x
            self.y0 = y
 
            
    class BackgroundDisplayable(renpy.Displayable):
        def __init__(self, points, world_width, world_height, 
                     idle=None, hover=None, selected=None, **kwargs):
            super(BackgroundDisplayable, self).__init__()
        
            self.points = points
            self.world_width = world_width
            self.world_height = world_height
        
            self.idle = renpy.easy_displayable(idle)
            self.hover= renpy.easy_displayable(hover)
            self.selected = renpy.easy_displayable(selected)
            
            self.point_distance = (10, 10)

            self.half_width = self.total_width * 0.5
            self.half_height = self.total_height * 0.5

            self.sphere_area = 140
            
        @property
        def total_width(self):
            return self.world_width * self.point_distance[0]
            
        @property
        def total_height(self):
            return self.world_height * self.point_distance[1]            
            
        def render(self, width, height, st, at):
            render = renpy.Render(self.total_width, self.total_height)
            
            px = pointer.ex
            py = pointer.ey

            d_width = self.point_distance[0]
            d_height = self.point_distance[1]
            half_width = self.half_width
            half_height = self.half_height

            for point in self.points:
                x0d = point.x0 * d_width
                y0d = point.y0 * d_height
            
                point.dx = px - x0d + half_width - pointer.sensor[0]
                point.dy = py - y0d + half_height - pointer.sensor[1]

                point.dist = hypot(point.dx, point.dy)

                if point.dist < self.sphere_area:
                    d = self.hover
                
                elif point.c:
                    d = self.selected

                else:
                    d = self.idle

                # Draw dot
                render.place(d, x0d, y0d, width=d_width, height=d_height)

            return render

  
    class GlobeDisplayable(renpy.Displayable):
        def __init__(self, points, world_width, world_height, idle=None, selected=None, **kwargs):
            super(GlobeDisplayable, self).__init__()
        
            self.points = points
            self.world_width = world_width
            self.world_height = world_height

            self.idle = renpy.easy_displayable(idle)
            self.selected = renpy.easy_displayable(selected)
            
            self.point_distance = (10, 10)

            self.mod_pi = 0.5 * math.pi
            self.sphere_area = 140
        
            # Pre-calculate Transforms for scaling
            self.scales = list(self.generate_transforms(self.idle))
            self.c_scales = list(self.generate_transforms(self.selected))
        
        @property
        def total_width(self):
            return self.world_width * self.point_distance[0]
            
        @property
        def total_height(self):
            return self.world_height * self.point_distance[1]                
        
        @property
        def half_width(self):
            return self.total_width * 0.5
            
        @property
        def half_height(self):
            return self.total_height * 0.5            
        
        def generate_transforms(self, displayable):
            for x in range(1, self.sphere_area + 1):
                s = cos(self.mod_pi * x / self.sphere_area)
                yield Transform(displayable, zoom=s)

        def render(self, width, height, st, at):
            render = renpy.Render(0, 0)

            px = pointer.ex
            py = pointer.ey
            d_width = self.point_distance[0]
            d_height = self.point_distance[1]
            half_width = self.half_width
            half_height = self.half_height
            
            for point in self.points:
                
                if point.dist < self.sphere_area:
                
                    # Calculate projection
                    x0d = point.x0 * d_width
                    y0d = point.y0 * d_height
                
                    scale = cos(self.mod_pi * point.dist / self.sphere_area)
                    point.x = x0d - (point.dx * scale) - px - half_width + pointer.sensor[0]
                    point.y = y0d - (point.dy * scale) - py - half_height + pointer.sensor[1]

                    # Get the correct Transform
                    i = int(point.dist)
 
                    if point.c:
                        d = self.c_scales[i]
                    else:
                        d = self.scales[i]
                    
                    render.place(d, point.x, point.y)

            return render


    class Pointer(renpy.Displayable):
        def __init__(self, points, sensor, flat, globe, x=0, y=0, ex=0, ey=0):
            super(Pointer, self).__init__()

            self.points = points
            self.sensor = sensor
            self.flat = flat
            self.globe = globe
            
            self.x = x
            self.y = y
            self.ex = ex
            self.ey = ey
            
            self.fixed = Fixed(Solid("#333"))
            
            d = Image("bg_dot.png")
            red_matrix = im.matrix.colorize("#fff", "#f00")
            self.center = im.MatrixColor(d, red_matrix)
            
        def render(self, width, height, st, at):
            render = renpy.Render(config.screen_width, config.screen_height)

            # Easing
            self.ex += (self.x - self.ex) / 15
            self.ey += (self.y - self.ey) / 15
       
            # V line
            render.place(self.fixed, self.ex - 2, 0, width=4)
            
            # H line
            render.place(self.fixed, 0, self.ey - 2, height=4)

            # Center
            render.place(self.center, self.ex - 4, self.ey - 4, width=10, height=10)            
            
            # If the cursor is centered, stop redrawing
            if not int(self.x) == int(self.ex) and not int(self.y) == int(self.ey):
                renpy.redraw(self.flat, 0)
                renpy.redraw(self.globe, 0)

            renpy.redraw(self, 0)

            return render

        def event(self, ev, x, y, st):
            
            self.x = x
            self.y = y

            if ev.type == pygame.MOUSEBUTTONDOWN:
                dm = 9999
                c = None
                for point in self.points:
                    
                    dx = point.x - self.x + config.screen_width * 0.5
                    dy = point.y - self.y + config.screen_height * 0.5
                    d = hypot(dx, dy)

                    if d < 10:
                        if d < dm:
                            dm = d
                            c = point
                            break

                if c:
                    c.c = True
                    renpy.redraw(self.flat, 0)
                    renpy.redraw(self.globe, 0)


init python:
    world = (
    "000000000001111110001100000011000100000000000000"
    "001100011111001100001110011111111110000000000000"
    "111111111001011001001111111111111111111100000000"
    "111111111011000001100111111111111111111000000000"
    "000111111111000000111111111111111111101000000000"
    "000111111111000001111111111111111111110000000000"
    "001111111000000001101011111111111111010000000000"
    "000111111000000000100000111111111111010000000000"
    "000111010000000001111111111111111111010000000000"
    "000011101000000011111111111001111111000000000000"
    "000001100000000011111111110001100110100000000000"
    "000000011110000001111111110000100001100000000000"
    "000000011111000000001111110000000111100000000000"
    "000000011111110000001111100000010111001100000000"
    "000000011111110000001111100000001001010000000000"
    "000000001111110000001111010000000000111100000000"
    "001000000111100000001111010000000011111100000000"
    "000000000111000000000110000000000001111100000000"
    "000000000110000000000000000000000000011001000000"
    "000000000110000000000000000000000000000010000000"
    "000000000110000000000000000000000000000000000000"
    "000000000010000000000000000000000000000000000000")

    points = list(get_points(world, width=48, height=22))
    
    bg_dot = Image("bg_dot.png")

    light_grey_matrix = im.matrix.colorize("#fff", "#666")    
    dark_grey_matrix = im.matrix.colorize("#fff", "#333")
    orange_matrix = im.matrix.colorize("#fff", "#f80")

    light_grey_dot = im.MatrixColor(bg_dot, light_grey_matrix)    
    dark_grey_dot = im.MatrixColor(bg_dot, dark_grey_matrix)
    orange_dot = im.MatrixColor(bg_dot, orange_matrix)

    b = BackgroundDisplayable(
        points, 
        48,
        22,
        idle=light_grey_dot,
        hover=dark_grey_dot,
        selected=orange_dot
    )
    
    circle = Image("circle.png")
    orange_matrix = im.matrix.colorize("#fff", "#f83")
    orange_circle = im.MatrixColor(circle, orange_matrix)

    g = GlobeDisplayable(points, 48, 22, idle=circle, selected=orange_circle)
    
    pointer = Pointer(points, (config.screen_width * 0.5, config.screen_height * 0.5), b, g)

    
screen world:
    add b:
        xalign 0.5
        yalign 0.5
    add g:
        xalign 0.5
        yalign 0.5

    add pointer
    vbox:
        text "Globe Area"
        bar value 140 adjustment ui.adjustment(1000, 140, adjustable=True, changed=alter_area)
        
        text "Point Distance"
        bar value 10 adjustment ui.adjustment(100, 10, adjustable=True, changed=alter_point_distance)
   
    
## The game starts here.

label start:

    call screen world

    return
