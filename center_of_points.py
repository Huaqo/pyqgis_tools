from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsFields, QgsField, QgsWkbTypes
from qgis.PyQt.QtCore import QVariant

layer = iface.activeLayer()

sum_x = 0
sum_y = 0
count = 0

for feature in layer.getFeatures():
    geom = feature.geometry()
    if geom.isMultipart():
        points = geom.asMultiPoint()
    else:
        points = [geom.asPoint()]
    for point in points:
        sum_x += point.x()
        sum_y += point.y()
        count += 1
      
mean_x = sum_x / count
mean_y = sum_y / count
centroid_point = QgsGeometry.fromPointXY(QgsPointXY(mean_x, mean_y))

crs = layer.crs().authid()  
new_layer = QgsVectorLayer(f"Point?crs={crs}", "Centroid Layer", "memory")
new_layer_data_provider = new_layer.dataProvider()
new_layer_data_provider.addAttributes([QgsField("id", QVariant.Int)])
new_layer.updateFields()
new_feature = QgsFeature()
new_feature.setGeometry(centroid_point)
new_feature.setAttributes([1])
new_layer_data_provider.addFeature(new_feature)
new_layer.updateExtents()

QgsProject.instance().addMapLayer(new_layer)

print(f"New layer 'Centroid Layer' created withcentroid at: ({mean_x}, {mean_y})")
