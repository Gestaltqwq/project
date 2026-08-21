import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
np.random.seed(42)
n_samples = 1000
housing = fetch_california_housing()
df = pd.DataFrame(housing.data,columns=housing.feature_names)
df['target'] = housing.target
print("\n数据前5行:")
print(df.head())
print("\n数据统计描述:")
print(df.describe())

feature_cols = housing.feature_names
X = df[feature_cols].values
y = df['target'].values

X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

models = {
    '线性回归': LinearRegression(),
    '决策树': DecisionTreeRegressor(max_depth=6,random_state=42),
    '随机森林': RandomForestRegressor(n_estimators=100,max_depth=10,random_state=42)
}

results = []
predictions = {}

for name,model in models.items():
    if name == '线性回归':
        model.fit(X_train_scaled,y_train)
        y_pred = model.predict(X_test_scaled)
    else:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

    predictions[name] = y_pred

    mse = mean_squared_error(y_test,y_pred)
    r2 = r2_score(y_test,y_pred)

    results.append({
        '模型':name,
        "mse":round(mse,4),
        'r2':round(r2,4)
    })

df_results = pd.DataFrame(results).set_index('模型')
print(df_results)

best_r2 = df_results['r2'].idxmax()
best_mse = df_results['mse'].idxmin()

rf_model = models['随机森林']
feature_importances = rf_model.feature_importances_
importance_df = pd.DataFrame({
    '特征': feature_cols,
    '重要性': feature_importances
}).sort_values('重要性', ascending=False)

for i,row in importance_df.iterrows():
    print(f"{row['特征']:2-s},{row['重要性']:.4f}")