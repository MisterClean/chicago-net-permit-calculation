"""Point-in-polygon for official ward GeoJSON, including polygon holes.

Latitude edge buckets accelerate the standard ray-casting algorithm. Boundary
points are returned separately rather than assigned an arbitrary ward.
"""
import math


def prepare_ring(coordinates):
    xs=[p[0] for p in coordinates]; ys=[p[1] for p in coordinates]
    low,high=min(ys),max(ys)
    step=(high-low)/128 if high>low else 1
    buckets=[[] for _ in range(129)]
    for start,end in zip(coordinates,coordinates[1:]+coordinates[:1]):
        x1,y1=start; x2,y2=end
        edge=(x1,y1,x2,y2)
        first=max(0,min(128,int((min(y1,y2)-low)/step)))
        last=max(0,min(128,int((max(y1,y2)-low)/step)))
        for index in range(first,last+1): buckets[index].append(edge)
    return {'bbox':(min(xs),low,max(xs),high),'low':low,'step':step,'buckets':buckets}


def in_ring(x,y,ring):
    left,bottom,right,top=ring['bbox']
    if not(left<=x<=right and bottom<=y<=top): return False,False
    index=max(0,min(128,int((y-ring['low'])/ring['step'])))
    inside=False
    for x1,y1,x2,y2 in ring['buckets'][index]:
        if y1==y2:
            if abs(y-y1)<1e-10 and min(x1,x2)<=x<=max(x1,x2):return False,True
            continue
        if (y1>y)!=(y2>y):
            crossing=x1+(y-y1)*(x2-x1)/(y2-y1)
            if abs(crossing-x)<1e-10:return False,True
            if x<crossing:inside=not inside
    return inside,False


def prepare_wards(geojson):
    wards=[]
    for feature in geojson['features']:
        geometry=feature['geometry']; polygons=geometry['coordinates']
        if geometry['type']=='Polygon':polygons=[polygons]
        if geometry['type'] not in ['Polygon','MultiPolygon']: raise ValueError(geometry['type'])
        properties=feature['properties']
        ward=int(properties.get('ward',properties.get('ward_number')))
        rings=[[prepare_ring(ring) for ring in polygon] for polygon in polygons]
        wards.append((ward,rings))
    return wards


def assign_ward(longitude,latitude,wards):
    try:x,y=float(longitude),float(latitude)
    except (TypeError,ValueError):return None,'missing_coordinates'
    if not(math.isfinite(x) and math.isfinite(y)):return None,'invalid_coordinates'
    matches=[]
    for ward,polygons in wards:
        for polygon in polygons:
            outer,boundary=in_ring(x,y,polygon[0])
            if boundary:return None,'on_boundary'
            if not outer:continue
            in_hole=False
            for ring in polygon[1:]:
                inside,boundary=in_ring(x,y,ring)
                if boundary:return None,'on_boundary'
                if inside:in_hole=True;break
            if not in_hole:matches.append(ward);break
    return (matches[0],'matched') if len(matches)==1 else (None,'outside_wards' if not matches else 'overlapping_wards')
