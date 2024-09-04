from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsFeature, QgsField, QgsGeometry, QgsVectorLayer, QgsProject)
import requests
import geopandas as gpd

# Parameters (Set these manually in the script)
country_code = 'DEU'  # Country code (ISO-3)
boundary_type = 'ADM0'  # Boundary type (ADM0, ADM1, ADM2, etc.)
release_type = 'gbOpen'  # Release type ('gbOpen', 'gbHumanitarian', 'gbAuthorative')

# Function to fetch geoboundary data
def fetch_geoboundary(release_type, country_code, boundary_type):
    api_url = f"https://www.geoboundaries.org/api/current/{release_type}/{country_code}/{boundary_type}/"
    try:
        response = requests.get(api_url)
        if response.status_code != 200:
            print(f"Failed to fetch data: HTTP Status Code {response.status_code}")
            return None

        data = response.json()
        results = []
        
        if not isinstance(data, list):
            data = [data]

        for country_data in data:
            if 'gjDownloadURL' not in country_data:
                print(f"'gjDownloadURL' not found for {country_data.get('boundaryISO', 'unknown country')}")
                continue

            geojson_url = country_data['gjDownloadURL']
            gdf = gpd.read_file(geojson_url)
            if gdf.empty:
                print(f"Loaded GeoDataFrame for {country_code} is empty.")
                continue

            metadata = {key: country_data.get(key, '') for key in country_data}
            results.append({'gdf': gdf, 'metadata': metadata})

        return results

    except requests.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return None

# Fetch geoboundary data
results = fetch_geoboundary(release_type, country_code, boundary_type)

if not results:
    raise Exception('Failed to fetch geoBoundary data')

# Create a new memory layer to store the boundary data
layer_name = f"{country_code}_{boundary_type}_{release_type}_geoBoundaries"
vector_layer = QgsVectorLayer("Polygon?crs=epsg:4326", layer_name, "memory")
pr = vector_layer.dataProvider()

# Define fields for the new layer if needed
pr.addAttributes([QgsField("id", QVariant.Int)])
vector_layer.updateFields()

# Loop over the fetched data and add features to the new layer
for result in results:
    gdf = result['gdf']

    for index, row in gdf.iterrows():
        # Check if the row has a valid geometry
        if not hasattr(row['geometry'], 'wkt'):
            print(f"Unexpected geometry type for row {index}")
            continue

        # Create a new feature and set the geometry from the WKT
        feat = QgsFeature()
        try:
            feat.setGeometry(QgsGeometry.fromWkt(row['geometry'].wkt))
            feat.setAttributes([index])  # Set any attributes if necessary
            pr.addFeature(feat)
        except Exception as e:
            print(f"Error setting geometry from WKT: {e}")
            continue

# Update the layer's extents
vector_layer.updateExtents()

# Add the new layer to the QGIS project
QgsProject.instance().addMapLayer(vector_layer)

print(f"GeoBoundary layer '{layer_name}' added to the project.")
