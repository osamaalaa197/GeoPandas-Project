import streamlit as st
import geopandas as gpd
import leafmap.foliumap as leafmap
import requests
import shutil
import os
import subprocess
import folium
import json
import streamlit.components.v1 as components
import base64
import sys

def folium_static(map, width=700, height=500):
    """Display folium map in Streamlit app"""
    map.add_child(folium.LatLngPopup())  # add popup to show lat-long coordinates
    map._repr_html_ = map.get_root().render()
    components.html(
        f'<iframe src="data:text/html;base64,{base64.b64encode(map._repr_html_.encode()).decode()}" width={width} height={height} frameborder="0" scrolling="no"></iframe>',
        height=height+15,  # add extra height to account for the popup
        scrolling=False,
    )  




headers = {
    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
}

st.set_page_config(page_title="GeoPandas Project")
st.header("Wlecome to My APP, Please select the operation you wish to perform from the options below..")
option = st.selectbox(
    'pick your choose?',
    ('conversion file to anther format', 'get the shortest route', 'downloading the intersection, union and erase between two layers','Risk assessment'))
if option=="conversion file to anther format":
    inputFile = st.file_uploader("upload Your file that do you want to convert ",type="GeoJSON")
    filename = st.text_input("Enter a name for the output file")
    if inputFile and filename:
            jsonfile = gpd.read_file(inputFile).to_crs('EPSG:3857')
            secondOption = st.selectbox(
            'please select the format?',
            ('Shapefile', 'Geopakage', 'Geodatabase'))
            if secondOption=='Shapefile':
                    os.makedirs(f"{filename}-ShpFiles")
                    jsonfile.to_file(f"{filename}-ShpFiles/{filename}.shp")
                    shutil.make_archive(f"{filename}-ShpFiles", "zip", f"{filename}-ShpFiles")
                    with open(f"{filename}-ShpFiles.zip", "rb") as shpFile:
                        st.download_button(
                            label = 'convert file to ShpFiles ',
                            file_name = f"{filename}ShpFile.zip",
                            data = shpFile                           
                        )
                    shutil.rmtree(f"{filename}-ShpFiles")
                    os.remove(f"{filename}-ShpFiles.zip")
            elif secondOption=='Geopakage':
                    jsonfile.to_file(f"{filename}.gpkg")
                    with open(f"{filename}.gpkg", "rb") as Geopakage:
                        st.download_button(
                            label = 'convert file to Geopackage ',
                            file_name = f"{filename}.gpkg",
                            data = Geopakage
                        )
                    os.remove(f"{filename}.gpkg")
            elif secondOption=='Geodatabase':
                    # to convert to geodata base once convert file to Geopackage then use ogr to convert shp to geodatabase
                    jsonfile.to_file(f"{filename}.gpkg")
                    subprocess.call(f"ogr2ogr {filename}.gdb {filename}.gpkg")
                    shutil.make_archive(f"{filename}.gdb", "zip", f"{filename}.gdb")
                    with open(f"{filename}.gdb.zip","rb") as Geodatabase:
                        st.download_button(
                            label = 'convert file to Geodatabase ',
                            file_name = f"{filename}.gdb.zip",
                            data = Geodatabase
                        )
                    shutil.rmtree(f"{filename}.gdb")         
                    os.remove(f"{filename}.gpkg")
                    os.remove(f"{filename}.gdb.zip")      
          
elif option=="get the shortest route":
    #get the shortest route
    inputFile = st.file_uploader("upload Your Points",type="GeoJSON")
    if inputFile:
        file_cntent=inputFile.read()
        file_contents_str = file_cntent.decode('utf-8')
        data=json.loads(file_contents_str)
        m = folium.Map(location=[data['features'][0]['geometry']['coordinates'][1], data['features'][0]['geometry']['coordinates'][0]], zoom_start=15)
        allCoordForFeature=[]
        counterofpoint=0
        for feature in data ["features"]:
            if feature['geometry']['type']=='Polygon':
                st.write("Please upload a file with type Point")
                sys.exit(1)
            elif feature['geometry']['type']=='Point':
                cood=feature['geometry']['coordinates']
                lat=cood[1]
                long=cood[0]
                counterofpoint+=1
                thisdict = {
                "counter":counterofpoint,
                "lat":float(lat) ,
                "long": float(long),
                }
                allCoordForFeature.append(thisdict)
                # st.write(f"lat :{lat},log:{long}")
                folium.Marker(location=[lat,long],popup=counterofpoint,tooltip="click for more information").add_to(m)
        folium_static(m)
        allCoords = [(coord['lat'], coord['long'],coord['counter']) for coord in allCoordForFeature]
        # st.write(allCoords)
        fristpoint = st.selectbox(
        'please enter the frist point',
        allCoords)
        fristpoint=list(fristpoint)
        # st.write(fristpoint)
        secondpoint = st.selectbox(
        'please enter the second point',
        allCoords)
        secondpoint=list(secondpoint)
        # st.write(type(secondpoint))
        if st.button("Show me the route") and fristpoint != secondpoint:        
                call = requests.get(f'https://api.openrouteservice.org/v2/directions/driving-car?api_key=5b3ce3597851110001cf6248c9ee9bd765a84956a2f95235ab20013b&start=%20%20%20%20%20%20%20%20%20%20{fristpoint[1]},{fristpoint[0]}&end=%20%20%20%20%20%20%20%20%20%20{secondpoint[1]},{secondpoint[0]}', headers=headers)
                df =gpd.read_file(call.text)
                geojson = folium.GeoJson(df)
                geojson.add_to(m)
                folium_static(m)
elif option=="downloading the intersection, union and erase between two layers":
    fristFile = st.file_uploader("upload the frist file",type="GeoJSON")
    secondFile = st.file_uploader("upload the second file",type="GeoJSON")
    if fristFile and secondFile:
        choice = st.radio(
        "pick your choice",
        ('intersection', 'Erase', 'union'))
        if choice=='intersection':
                # frist_gfile = gpd.read_file(fristFile)
                frist_gfile = gpd.read_file(fristFile).to_crs('EPSG:3857')
                # second_gfile=gpd.read_file(inputFile)
                second_gfile = gpd.read_file(secondFile).to_crs('EPSG:3857')
                intersection = gpd.overlay(frist_gfile, second_gfile, how='intersection')
                intersection.to_file('intersection.geojson', driver='GeoJSON')
                with open(f"intersection.geojson", "rb") as interGeo:
                        st.download_button(label='Download your Intersection',
                                        data=interGeo,
                                        file_name='intersection.geojson')
                os.remove(f"intersection.geojson")
                m = leafmap.Map()
                m.add_gdf(frist_gfile)
                m.add_gdf(second_gfile)
                m.add_gdf(intersection)
                m.to_streamlit(height=500)
        elif choice=='Erase':
                frist_gfile = gpd.read_file(fristFile).to_crs('EPSG:3857')
                second_gfile = gpd.read_file(secondFile).to_crs('EPSG:3857')
                erase = gpd.overlay(frist_gfile, second_gfile, how='difference')
                erase.to_file('erase.geojson', driver='GeoJSON')
                with open(f"erase.geojson", "rb") as Erase:
                        st.download_button(label='Download your Erase',
                                        data=Erase,
                                        file_name='erase.geojson')
                os.remove(f"erase.geojson")
                m = leafmap.Map()
                m.add_gdf(frist_gfile)
                m.add_gdf(second_gfile)
                m.add_gdf(erase)
                m.to_streamlit(height=500)
        elif choice=='union':
                frist_gfile = gpd.read_file(fristFile).to_crs('EPSG:3857')
                second_gfile = gpd.read_file(secondFile).to_crs('EPSG:3857')
                union = gpd.overlay(frist_gfile, second_gfile, how='union')
                union.to_file('union.geojson', driver='GeoJSON')
                with open(f"union.geojson", "rb") as unionfile:
                        st.download_button(label='Download your union',
                                        data=unionfile,
                                        file_name='union.geojson')
                os.remove(f"union.geojson")
                m = leafmap.Map()
                m.add_gdf(frist_gfile)
                m.add_gdf(second_gfile)
                m.add_gdf(union)
                m.to_streamlit(height=500)
elif option=="Risk assessment":
    st.header("Risk assessment")
    st.subheader("In this analysis, the first input represents the hazardous source, the second input represents the range of its risk buffer, and the third input represents the area being tested")
    risk_sources = st.file_uploader("please upload the risk sources",type="GeoJSON")
    buffersize=st.number_input('Insert buffer size')
    test_area = st.file_uploader("please upload the tested area",type="GeoJSON")
    if risk_sources and buffersize and test_area:
        risk_sources = gpd.read_file(risk_sources).to_crs('EPSG:3857')
        risk_sources = risk_sources[risk_sources.geometry.geom_type == "Point"]
        test_area = gpd.read_file(test_area).to_crs('EPSG:3857')
        test_area = test_area[test_area.geometry.geom_type == "Polygon"]
        buffer=risk_sources.buffer(buffersize)
        buffer= gpd.GeoDataFrame(geometry=buffer)
        intersection = gpd.overlay(buffer, test_area, how='intersection')
        intersection.to_file('bufferintersection.geojson', driver='GeoJSON')
        with open(f"bufferintersection.geojson", "rb") as unionfile:
                        st.download_button(label='Download your bufferintersection',
                                        data=unionfile,
                                        file_name='bufferintersection.geojson')
        os.remove(f"bufferintersection.geojson")
        m = leafmap.Map()
        m.add_gdf(risk_sources)
        m.add_gdf(test_area)
        m.add_gdf(buffer)
        m.add_gdf(intersection)
        m.to_streamlit(height=500)

    

            

        

    







        
    


  


        










            

            
            
            
          
            
