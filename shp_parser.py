import struct, os, time, pickle

def read(file_obj,position,type="d",endianness="l",raw_bytes=None):
    file_obj.seek(position)
    if raw_bytes is not None:
        return file_obj.read(raw_bytes)
    if type == "d" and endianness == "l":
        return struct.unpack("<d" ,file_obj.read(8))[0]
    elif type == "d" and endianness == "b":
        return struct.unpack(">d" ,file_obj.read(8))[0]
    elif type == "i" and endianness == "l":
        return struct.unpack("<i" ,file_obj.read(4))[0]
    elif type == "i" and endianness == "b":
        return struct.unpack(">i" ,file_obj.read(4))[0]
    else:
        print("Unsupported data type!")
        return -1
    

def readHeader(file_obj, output=0):
    f = file_obj
    code = read(f,0,"i","b")
    read(f,0,"i")
    read(f,0,"i")
    read(f,0,"i")
    read(f,0,"i")
    read(f,0,"i")
    length = read(f,24,"i","b")
    version = read(f,28,"i")
    shp_type = read(f,32,"i")
    Xmin = read(f,36)
    Ymin = read(f,44)
    Xmax = read(f,52)
    Ymax = read(f,60)
    Zmin = read(f,68)
    Zmax = read(f,76)
    Mmin = read(f,84)
    Mmax = read(f,92)

    if output:
        return [length,shp_type]
    
    print("File Code:",code)
    print("File Length:",length)
    print("File Version",version)
    print("Shape Type:",shp_type)
    print("Bounding Box: (%2.4f,%2.4f) (%2.4f,%2.4f)" % (Xmin,Ymin,Xmax,Ymax))
    print("Zmin:",Zmin)
    print("Zmax:",Zmax)
    print("Mmin:",Mmin)
    print("Mmax:",Mmax)



def readIndexFile(file):
    with open(file, 'rb') as f:
        offsets = []
        lengths = []
        position = 100
        file_length = (readHeader(f,1)[0]*2) - 96*2
        while(file_length > 0):
            offsets.append(read(f,position,"i","b"))
            position += 4
            lengths.append(read(f,position,"i","b"))
            position += 4
            file_length -= 8
        return offsets, lengths


def readRecord(filename,index,type=3,bounds=None):
    start = time.perf_counter()
    with open(os.path.join(filename+".shp"), 'rb') as f:
        offsets, lengths = readIndexFile(os.path.join(filename+".shx"))
        position = offsets[index]*2+8
        shp_type = read(f,position,"i")
        position += 4
        if shp_type != type:
            print("Unsupported record type! (%i)" % (shp_type))
        Xmin = read(f,position)
        position += 8
        Ymin = read(f,position)
        position += 8
        Xmax = read(f,position)
        position += 8
        Ymax = read(f,position)
        position += 8
        if bounds != None:
            if  Xmin < bounds[0] or Ymin < bounds[1] or Xmax > bounds[2] or Ymax > bounds[3]:
                finish = time.perf_counter()
                print(f'Exiting at {round(finish-start, 5)} seconds')
                return None
        numparts = read(f,position,"i")
        position += 4
        numpoints = read(f,position,"i")
        position += 4
        parts = []
        for i in range(numparts):
            parts.append(read(f,position,"i"))
            position += 4
        readpoints = 0
        temp = []
        points = []
        while(readpoints != numpoints):
            x = read(f,position)
            position += 8
            y = read(f,position)
            position += 8
            temp.append([y,x])
            readpoints += 1
        for i in range(len(parts)):
            try:
                points.append(temp[parts[i]:parts[i+1]])
            except:
                points.append(temp[parts[i]:])
        finish = time.perf_counter()
        print(f'Finished fetching content at index in {round(finish-start, 5)} seconds')
        return points


def getLines(filename,type=3,bounds=None):
    init_start = time.perf_counter()
    with open(os.path.join(filename+".shp"), 'rb') as f:
        lines = []
        offsets, lengths = readIndexFile(os.path.join(filename+".shx"))
        curr_index = 0

        # skip header
        f.read(100)

        for index in range(len(offsets)):
            skip = False
            start = time.perf_counter()

            # skip content index
            f.read(8)

            shp_type = struct.unpack("<i",f.read(4))[0]
            if shp_type != type:
                print("Unsupported record type! (%i)" % (shp_type))
                return -1
            Xmin, Ymin, Xmax, Ymax = struct.unpack("<dddd",f.read(32))
            if bounds != None:
                if  Xmin < bounds[0] or Ymin < bounds[1] or Xmax > bounds[2] or Ymax > bounds[3]:
                    finish = time.perf_counter()
                    # print(f'Content out of bounds!  {round(finish-start, 5)} seconds')
                    f.read(lengths[curr_index]*2-36)
                    curr_index += 1
                    skip = True
            
            if not skip:
                numparts, numpoints = struct.unpack("<ii",f.read(8))
                parts = []
                for i in range(numparts):
                    parts.append(struct.unpack("<i",f.read(4))[0])
                readpoints = 0
                temp = []
                
                while(readpoints != numpoints):
                    x,y = struct.unpack("<dd",f.read(16))
                    temp.append([y,x])
                    readpoints += 1
                
                if numparts > 0:
                    for i in range(len(parts)):
                        try:
                            lines.append([temp[parts[i]:parts[i+1]]])
                        except:
                            lines.append([temp[parts[i]:]])

                finish = time.perf_counter()
                #print(f'Read content at {curr_index} in {round(finish-start, 5)} seconds')
                curr_index += 1

        finish = time.perf_counter()
        print(f'Finished fetching all roads within specified bounds in {round(finish-init_start, 3)} seconds')
        return lines


def getPoints(filename,type=1,bounds=None):
    init_start = time.perf_counter()
    with open(os.path.join(filename+".shp"), 'rb') as f:
        points = []
        offsets, lengths = readIndexFile(os.path.join(filename+".shx"))
        curr_index = 0

        # skip header
        f.read(100)

        for index in range(len(offsets)):
            skip = False
            # start = time.perf_counter()

            # skip content index
            f.read(8)

            shp_type = struct.unpack("<i",f.read(4))[0]
            if shp_type != type:
                print("Unsupported record type! (%i)" % (shp_type))
                return -1
        
            x, y = struct.unpack("<dd",f.read(16))

            if bounds != None:
                if  x < bounds[0] or y < bounds[1] or x > bounds[2] or y > bounds[3]:
                    # finish = time.perf_counter()
                    # print(f'Content out of bounds!  {round(finish-start, 5)} seconds')
                    f.read(lengths[curr_index]*2-20)
                    curr_index += 1
                    skip = True
            
            if not skip:
                points.append([y,x])

                # finish = time.perf_counter()
                # print(f'Read content at {curr_index} in {round(finish-start, 5)} seconds')
                curr_index += 1

        finish = time.perf_counter()
        print(f'Finished fetching all points within specified bounds in {round(finish-init_start, 3)} seconds')
        return points


# readIndexFile("./tl_2021_47157_roads.shx", )
# readRecord("./tl_2021_47157_roads",1)


# For every road in the bounding box, return the polylines
# temp = []
# for i in range(20):
#     record = readRecord("./tl_2021_47157_roads",i,bounds=[-89.872580,35.101027,-89.787396,35.140670])
#     if record is not None:
#         temp.append(record)
# print((temp))


def output(roads):
    for road in roads:
        for part in road:
            print(part)


def outputRoads():
    # lines = getLines("./tl_2021_47157_roads")
    # lines = getLines("./tl_2021_47157_roads",bounds=[-89.872580,35.101027,-89.787396,35.140670])
    # lines = getLines("./tl_2021_47157_roads",bounds=[-89.930332,35.083770,-89.723316,35.164840])
    # lines = getLines("./OSM_Roads_Agricenter")
    # lines = getLines("./clipped_osm_agricenter_roads")
    # lines = getLines("./OSM_memphis_clipped",bounds=[-90.075361,35.064913,-89.730661,35.218752]) # Improved extent
    # lines = getLines("./OSM_memphis_clipped",bounds=[-90.07530,35.06490,-89.73070,35.21880]) # Slightly smaller extent
    lines = getLines("./OSM_memphis_clipped",bounds=[-90.0486,35.0719,-89.7320,35.2114]) # Slightly smaller extent
    #lines = getLines("./OSM_memphis_clipped",bounds=[-89.98,35.07,-89.73,35.20]) # Significantly smaller extent
    # lines = getLines("./OSM_memphis_clipped",bounds=[-89.9102,35.0923,-89.7318,35.1686]) # old agricenter-prod extent
    # lines = getLines("./OSM_memphis_clipped",bounds=[-89.877033,35.106055,-89.776970,35.151520]) # Extent Around Agricenter

    file = open(os.path.join('./extracted_roads.pkl'),'wb')
    pickle.dump(lines, file)


def outputTrees():
    points = getPoints("./Agricenter_Trees")

    file = open(os.path.join('./extracted_trees.pkl'),'wb')
    pickle.dump(points, file)


def outputBuildingLocations():
    points = getPoints("./TN_Building_Locations_Agricenter")

    file = open(os.path.join('./extracted_building_locations.pkl'),'wb')
    pickle.dump(points, file)


outputRoads()
# outputTrees()
# outputBuildingLocations()
# readHeader(open(os.path.join('./TN_Building_Locations_Agricenter.shp'),'rb'))