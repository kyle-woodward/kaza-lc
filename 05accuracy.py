#%%
# Asses Overall, Producer's, User's Accuracies using testing points,
# maybe also export a confusion matrix heatplot 
import ee
from sklearn import metrics
import os
from pathlib import Path
import pandas as pd

ee.Initialize()
sensor = "planet"
aoi_s = "Mufunta"
year = "2021"

labels = [0,1,2,3,4,5,6,7]

pred_LC_img = ee.Image(f"projects/sig-ee/WWF_KAZA_LC/output_landcover/{sensor}{aoi_s}{year}LandCover")

# EOSS's KAZA LC legend can be looked at here https:docs.google.com/document/d/12K4MqsAeq2bmCx3XyOMZefx6yBAkQv3lg_FA8NIxoow/edit?usp=sharing
    # aggregate LC2020 sub-classes together to make training points
    
    # Bare 60,61>>0
    # Built 50>> 1
    # Cropland 40>> 2
    # Forest 110,120,210>> 3
    # Grassland 31,32>> 4
    # Shrubs 130,222,231,232>> 5
    # Water 80,81>> 6
    # Wetland 90,91,92>> 7
    
# Until we have independently interpreted LC refrence samples, the ground truth is the collapsed EOSS LC product 
# we generated the training samples from, so the LANDCOVER property in the test points is the 'actual' for pred vs actual

test_pts = ee.FeatureCollection(f"projects/sig-ee/WWF_KAZA_LC/trainingPts/testing{aoi_s}{year}") 
print(test_pts.size().getInfo())
test_w_pred = pred_LC_img.sampleRegions(collection=test_pts,scale=10, projection='EPSG:32734', tileScale=2, geometries=True)

#print(test_w_pred.first().getInfo()['properties'])

pred = test_w_pred.aggregate_array('classification').getInfo()
true = test_w_pred.aggregate_array('LANDCOVER').getInfo()
print('samples per class in ground truth',test_pts.aggregate_histogram('LANDCOVER').getInfo())

# overall acc,prec,recall,f1
acc = metrics.accuracy_score(true,pred)
prec = metrics.precision_score(true,pred,average="weighted")
reca = metrics.recall_score(true,pred,average="weighted")
f1 = metrics.f1_score(true,pred,average="weighted")
print('Overall Metrics')
print(f'Accuracy: {acc}')
print(f'Precision: {prec}')
print(f'Recall: {reca}')
print(f'F1: {f1}')

# to get class-wise accuracies, must construct a confusion matrix 
mcm = metrics.multilabel_confusion_matrix(true, pred, sample_weight=None, labels=[0,1,2,3,4,5,6,7], samplewise=False)
# Returns list of 2x2 arrays of length labels 
# true negatives == arr[0][0]
# false negatives == arr[1][0]
# true positives == arr[1][1]
# false positives == arr[0][1]
omit_col, comit_col, prod, user = [],[],[],[]
for i in labels:
    print('Class', i)
    arr = mcm[i]
    true_neg = arr[0][0]
    false_neg = arr[1][0]
    true_pos = arr[1][1]
    false_pos = arr[0][1]
    
    omission = (false_neg / (false_neg + true_pos))
    comission = (false_pos / (false_neg + true_pos))
    print(f"Omission Error: {omission}")
    print(f"Comission Error: {comission}")
    prod_acc = round(100 - (omission*100),2) # Producers accuracy = 100% - Omission error
    user_acc = round(100 - (comission*100),2) # Users accuracy = 100% - Comission Error
    print(f"Producer's Accuracy: {prod_acc}")
    print(f"User's Accuracy: {user_acc}")
    omit_col.append(omission)
    comit_col.append(comission)
    prod.append(prod_acc)
    user.append(user_acc)


df_class = pd.DataFrame({'Class':labels, 'OmissionError':omit_col, 'ComissionError':comit_col, 'ProducerAcc':prod, 'UserAcc':user})    
df_oa = pd.DataFrame({'Accuracy':acc,'Precision':prec,'Recall':reca,'F1':f1})

cwd = os.getcwd()
output_path = Path(f"{cwd}/metrics_{sensor}_{year}_{aoi_s}")
if not os.path.exists(output_path):
    output_path.mkdir(parents=True)

df_class.to_csv(f"{output_path}/classAccuracy.csv")
df_oa.to_csv(f"{output_path}/overallAccuracy.csv") # don't need to make a df, see if you can write to a txt file

# %%
