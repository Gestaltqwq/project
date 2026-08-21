import seaborn as sns
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

sns.set_theme(style="whitegrid")

tips = sns.load_dataset("tips")
iris = sns.load_dataset("iris")

tips.to_csv("tips.csv")
iris.to_csv("iris.csv")


#tip直方图
plt.figure(figsize=(16, 10))
sns.histplot(tips,bins=30,kde=True)
plt.savefig("1.png")
plt.show()
#total_bill核密度图
plt.figure(figsize=(16, 10))
sns.kdeplot(data=tips,hue='smoker',x='total_bill')
plt.savefig("2.png")
plt.show()
#time箱线图
plt.figure(figsize=(16, 10))
sns.boxplot(data=tips,x='time',y='tip',hue='sex')
plt.savefig("3.png")
plt.show()
#time小提琴图
plt.figure(figsize=(16, 10))
sns.violinplot(data=tips,x='day',y='tip')
plt.savefig("4.png")
plt.show()
#tip柱状图
plt.figure(figsize=(16, 10))
sns.barplot(data=tips,x='day',y='tip',errorbar=None)
plt.savefig("5.png")
plt.show()
#热力图
plt.figure(figsize=(16, 10))
numeric_tips = tips.select_dtypes(include=['float64','int64'])
sns.heatmap(numeric_tips.corr(),annot=True,cmap="coolwarm")
plt.savefig("6.png")
plt.show()
#回归图
sns.lmplot(data=tips,x='total_bill',y='tip',hue='smoker')
plt.savefig("7.png")
plt.show()
#iris散点矩阵
sns.pairplot(data=iris[['sepal_length','sepal_width','petal_length','species']],hue='species')
plt.savefig("8.png")
plt.show()
#子图画布(2,1)
fig, axes=plt.subplots(2,1,figsize=(16,10))
sns.kdeplot(data=tips,x='total_bill',ax=axes[0])
sns.barplot(data=tips,x='sex',y='tip',hue='sex',ax=axes[1])
plt.tight_layout()
plt.savefig("9.png")
plt.show()
#子图画布(1,2)
fig, axes=plt.subplots(1,2,figsize=(16,10))
sns.violinplot(data=tips,x='sex',y='total_bill',hue='sex',ax=axes[0])
sns.barplot(data=tips,x='day',y='total_bill', ax=axes[1])
fig.suptitle("餐饮消费综合可视化图表")
plt.savefig("10.png")
plt.show()
