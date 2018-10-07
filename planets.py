import julian
import datetime
import math
import svgwrite
from svgwrite import cm, mm   
from jplephem.spk import SPK
#Dot Pluto's line

kernel = SPK.open('/Users/hanvakil/src/ephem/de430.bsp')
orbital_lengths = [0, 88, 225, 366, 687, 4333, 10759, 30689, 60182, 90560]
orbital_radii = [0, 0.9, 0.9, 0.95, 1.15, 1.15, 1.2, 1.25, 1.2, 1.75]
planet_radii = [0, 0.5, 0.7, 0.7, 0.6, 1.2, 1, 1, 1, 0.4]
orbit_sides = 500
radius_coefficients = [0, 1, 0.9, 0.95, 0.9, 0.95, 1, 1, 1.05, 1.05]
def make_orbits(start_date):
    orbits = []
    orbits += [False]
    
    for planet in range(1, 10):
        days_steps = orbital_lengths[planet]/orbit_sides
        date = start_date
        orbit = []
        aphelion = 0
        perihelion = 1e38
        for step in range(0, orbit_sides+1):
            date = start_date + datetime.timedelta(days=days_steps*step)
            eq = date_to_eq(date, planet)
            ec = equatorial_to_ecliptic(eq)
            angle = ecliptic_to_angle(eq)
            radius = ecliptic_to_radius(ec)
            if radius > aphelion:
                aphelion = radius
            if radius < perihelion:
                perihelion = radius
            orbit += [{"radius": radius, "angle": angle}]

            #print(step, date, angle, radius))

        for step in range(0, orbit_sides + 1):
            orbit[step]["radius"] = orbit[step]["radius"]/aphelion*orbital_radii[planet]

        orbits += [orbit]

#    print(orbits)
    return orbits;
    


# https://en.wikipedia.org/wiki/Ecliptic_coordinate_system#Converting_Cartesian_vectors
def equatorial_to_ecliptic(equatorial):
    obliquity = math.radians(23.5) 
    x = equatorial[0]
    y = math.cos(obliquity)*equatorial[1] + math.sin(obliquity)*equatorial[2]
    z = -math.sin(obliquity)*equatorial[1] + math.cos(obliquity)*equatorial[2]
    return [x,y,z]


def date_to_eq(date, planet):
    return kernel[0,planet].compute(julian.to_jd(date, fmt='jd'))

# strangely atan2 takes y, x as args rather than the other way around
def ecliptic_to_angle(ecliptic):
    return math.atan2(ecliptic[1], ecliptic[0])

def ecliptic_to_radius(ecliptic):
    return math.sqrt(ecliptic[1]*ecliptic[1] + ecliptic[0]*ecliptic[0])

def main(year,month,day):
    #Year in 4 digit format, month and day in 2 digit formant
    canvas = 400
    inter_orbit = 12
    innermost_orbit = 20
    max_planets = 9
    #date = datetime.datetime.strptime('1973-07-03', '%Y-%m-%d')
    #date = datetime.datetime.strptime('1988-06-19', '%Y-%m-%d')
    #date = datetime.datetime.strptime('2002-05-16', '%Y-%m-%d')
    #date = datetime.datetime.strptime('1991-10-04', '%Y-%m-%d')
    #date = datetime.datetime.strptime('2017-06-25', '%Y-%m-%d')
    #date = datetime.datetime.strptime('2010-04-16', '%Y-%m-%d')
    date = datetime.datetime.strptime(str(year)+'-'+str(month)+'-'+str(day), '%Y-%m-%d')

    dwg = svgwrite.Drawing("earth.svg", size=(canvas*mm, canvas*mm))
    #dwg.add(dwg.rect(insert=(0,0),size=(1133.858,1133.858),fill="green"))
    shapes = dwg.add(dwg.g(id='shapes', fill='none'))
    orbits = make_orbits(date+ datetime.timedelta(30))
    outer_cut = ((max_planets + 3) * inter_orbit + innermost_orbit)
    pluto = 9

    # sun
    shapes.add(dwg.circle(center=((canvas/2)*mm,(canvas/2)*mm), r=10*mm, stroke='red',fill='red', stroke_width=1*mm))
    '''for deg in range(int(2)):
        length = 5
        dist = 2
        x = (math.cos(deg) * (10 + dist)) + ((canvas/2))
        y = (math.sin(deg) * (10 + dist)) + ((canvas/2))
        x1 = (math.cos(deg) * (10 + dist + length))
        y1 = (math.sin(deg) * (10 + dist + length))
        shapes.add(dwg.line((x,y),(100,100),stroke="black"))'''
    for planet in range(1, max_planets+1):
        eq = date_to_eq(date, planet)
        ec = equatorial_to_ecliptic(eq)
        angle = ecliptic_to_angle(eq)
        orbit = (planet * inter_orbit + innermost_orbit) * radius_coefficients[planet]
        if planet == 2:
            orbit = (planet * (inter_orbit) + innermost_orbit)*0.9
        if planet==6:
            orbit = (planet * (inter_orbit) + innermost_orbit)
        planet_radius = 4 * planet_radii[planet]

        # orbit
        #shapes.add(dwg.circle(center=((canvas/2)*mm,(canvas/2)*mm), r=(orbit)*mm, stroke='black', stroke_width=0.2*mm))

        for step in range(0, orbit_sides):
            before = orbits[planet][step]['angle']
            after = orbits[planet][step+1]['angle']
            test_angle = angle
            planet_gap_rad = ((planet_radius * 2)/orbit) / orbits[planet][step]['radius']

            #print(step, planet, angle, before, after)
 
            if test_angle < 0 and not (before>0 and after>0):
                test_angle += math.pi

            if (before <= angle and after >= angle) or (before <= test_angle and after >= test_angle):
                if (outer_cut > orbit*orbits[planet][step]['radius']): # does pluto fall off the edge of disk?
                    shapes.add(dwg.circle(center=(((canvas/2)+orbits[planet][step]['radius']*math.sin(orbits[planet][step]['angle'])*orbit)*mm,
                                                  ((canvas/2)+orbits[planet][step]['radius']*math.cos(orbits[planet][step]['angle'])*orbit)*mm),
                                          r=planet_radius*mm, stroke='red',
                                          stroke_width=1*mm, fill = 'red'))
                if planet == 6:
                    for x in range(9):
                        if x != 4 and x!=0:
                            shapes.add(dwg.ellipse(center=(((canvas/2)+orbits[planet][step]['radius']*math.sin(orbits[planet][step]['angle'])*orbit)*mm,
                                                          (((canvas/2)+orbits[planet][step]['radius']*math.cos(orbits[planet][step]['angle'])*orbit)+0.5)*mm),
                                                  #r=(planet_radius*(1+(x+2)/8))*mm, (planet_radius*(1+(x+2)/8))*mm,
                                                  r=((planet_radius*(1+(x+2)/6))*mm,(planet_radius*(1+(x-17)/20))*mm),
                                                  stroke='red',
                                                  stroke_width=0.15*mm, fill = 'none'))
            else:
                before -= planet_gap_rad
                after += planet_gap_rad
                test_angle = angle

                # all this fiddling is to deal with gaps that go across the 0 -> -pi boundaries
                if(before < -math.pi):
                    after += math.pi*2
                    before += math.pi*2
                    if test_angle < 0:
                        test_angle += math.pi*2
                if(after > math.pi):
                    after -= math.pi*2
                    before -= math.pi*2
                    if test_angle > 0:
                        test_angle -= math.pi*2

                if ((before - after) > (math.pi*1)):
                    before -= math.pi*2
                # end fiddling
                if not (before <= test_angle and after >= test_angle):# or (before <= test_angle and after >= test_angle):
                    if (outer_cut > orbit*orbits[planet][step]['radius']): # does orbit fall off the edge of disk?
                        if planet != 9 or step%3 == 0:
                            shapes.add(dwg.line(start=(((canvas/2)+orbits[planet][step]['radius']*math.sin(orbits[planet][step]['angle'])*orbit)*mm,
                                                       ((canvas/2)+orbits[planet][step]['radius']*math.cos(orbits[planet][step]['angle'])*orbit)*mm),
                                                end=(((canvas/2)+orbits[planet][step+1]['radius']*math.sin(orbits[planet][step+1]['angle'])*orbit)*mm,
                                                     ((canvas/2)+orbits[planet][step+1]['radius']*math.cos(orbits[planet][step+1]['angle'])*orbit)*mm),
                                                stroke='black', stroke_width=0.2*mm))
                        
                
    sun_centered_cut = True
    if sun_centered_cut:
        shapes.add(dwg.circle(center=((canvas/2)*mm,(canvas/2)*mm),
                              r=outer_cut*mm,
                              stroke='blue', stroke_width=1*mm,fill = 'none'))    
    else:
        # outer cut (further out but around orbit of pluto)
        orbit = (pluto+2) * inter_orbit + innermost_orbit
        for step in range(0, orbit_sides):
            shapes.add(dwg.line(start=(((canvas/2)+orbits[pluto][step]['radius']*math.sin(orbits[pluto][step]['angle'])*orbit)*mm,
                                       ((canvas/2)+orbits[pluto][step]['radius']*math.cos(orbits[pluto][step]['angle'])*orbit)*mm),
                                end=(((canvas/2)+orbits[pluto][step+1]['radius']*math.sin(orbits[pluto][step+1]['angle'])*orbit)*mm,
                                     ((canvas/2)+orbits[pluto][step+1]['radius']*math.cos(orbits[pluto][step+1]['angle'])*orbit)*mm),
                                stroke='blue', stroke_width=1*mm,fill = 'none'))    
                          

    dwg.save()

main(2002,10,20)

