# %% [markdown]
# # Software Defect Prediction Model
# ### Based on NASA JM1 Dataset & Radon Metrics
# 
# ---
# 
# ## Project Overview
# This project implements a **Machine Learning model** designed to predict the probability of software defects within source code. 
# 
# The analysis is performed using **Static Code Metrics**, focusing on two industry-standard frameworks:
# * **McCabe’s Cyclomatic Complexity:** Measures the logical complexity and control flow of the program ($v(g)$).
# * **Halstead’s Software Science:** Measures computational complexity based on operators and operands (Volume, Effort, Difficulty).
# 
# **Goal:** To provide an automated risk assessment for code modules, allowing developers and AI agents to prioritize testing and code reviews.

# %% [markdown]
# ## 1. Environment Setup and Libraries Injection
# In this section, we import the essential Python libraries required for data manipulation, visualization, and machine learning. 
# * **Pandas & NumPy:** For efficient data handling and numerical operations.
# * **Matplotlib & Seaborn:** For exploratory data analysis and visual representation of data patterns.
# * **Scikit-Learn:** For data preprocessing, scaling, and implementing the Logistic Regression model.

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
%matplotlib inline

# %% [markdown]
# ## 2. Data Acquisition
# We load the **NASA JM1 dataset**, which contains over 10,000 instances of software modules. Each instance is described by multiple static code metrics. 
# At this stage, we also perform an initial check for data integrity and identify missing values (NaN) to ensure the dataset is clean before proceeding to analysis.

# %%
train = pd.read_csv('data/archive/jm1.csv')

# %%
# Displaying the first few rows to verify successful loading
train.head()

# %% [markdown]
# ** Use info and describe() on ad_data**

# %%
train.info()

# %% [markdown]
# ## 3. Feature Selection: Aligning with Radon Metrics
# To ensure the model is practical and compatible with our source code analysis tool (Radon), we narrow down the dataset to only include common metrics. 
# This selection focuses on **McCabe's LOC and Cyclomatic Complexity**, alongside **Halstead's core metrics**.

# %%
# 1. הגדרת העמודות שאנחנו רוצים להשאיר (כולל ה-Target)
selected_columns = ['loc', 'v(g)', 'v', 'd', 'e', 'b', 'defects']

# 2. יצירת DataFrame חדש ומצומצם
train = train[selected_columns].copy()

# 3. המרת ה-Target למספרים (0 ו-1)
train['defects'] = train['defects'].astype(int)

# 4. וידוא אחרון שהכל תקין
print("--- Selected Features Info ---")
print(train.info())

# %%
train.head()

# %% [markdown]
# # 4. Exploratory Data Analysis (EDA)
# 
# ## 4.1 Statistical Profiling
# In this step, we use `info()` and `describe()` to understand the data types, 
# detect missing values, and observe the statistical distribution of our features.

# %%
# הצגת הסטטיסטיקה התיאורית
stats = train.describe()
display(stats)

# חישוב אחוז הבאגים בדאטה-סט
bug_percentage = train['defects'].mean() * 100
print(f"\nTarget Distribution: {bug_percentage:.2f}% of modules contain defects.")

# %% [markdown]
# ### Key Insights from Statistics:
# 1. **Scale Imbalance:** Features like `Effort (e)` have magnitudes millions of times larger than `Bugs (b)`. Standard scaling is mandatory.
# 2. **Skewed Data:** High maximum values in `loc` (3442) and `v(g)` (470) compared to their medians suggest the presence of extreme outliers.
# 3. **Class Imbalance:** Only ~19.4% of the modules are defective. We must account for this during model training using class weighting.

# %% [markdown]
# ## 4.2 Correlation Analysis
# Now, we visualize the relationships between metrics using a heatmap. 
# This helps identify which code features are the most significant predictors for defects.

# %%
# חישוב מטריצת הקורלציה
plt.figure(figsize=(10, 8))
correlation_matrix = train.corr()

# יצירת ה-Heatmap
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
plt.title('Correlation Matrix of Code Metrics and Defects')
plt.show()

# %% [markdown]
# ### Feature Redundancy Identified
# The heatmap above reveals a correlation of **1.00** between `v` and `b`. 
# Since `b` (Halstead's delivered bugs) is a linear derivative of `v` (Volume), keeping both would introduce **Multicollinearity**. 
# To simplify the model, we will proceed with only the `v` feature.

# %%
train = train.drop(columns=['b'])

# %%
# חישוב מטריצת הקורלציה
plt.figure(figsize=(10, 8))
correlation_matrix = train.corr()

# יצירת ה-Heatmap
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
plt.title('Correlation Matrix of Code Metrics and Defects')
plt.show()

# %%
# יצירת Pairplot כדי לראות את הקשרים הויזואליים
# אנחנו משתמשים ב-hue כדי להבדיל בין מודולים עם ובלי באגים
sns.pairplot(train, hue='defects', diag_kind='kde', plot_kws={'alpha': 0.5, 's': 20})
plt.suptitle('Pairplot of Selected Metrics colored by Defects', y=1.02)
plt.show()

# %% [markdown]
# ### Insights from Pairplot:
# 1. **Overlap in Simple Modules:** In low-complexity regions (bottom-left), defective and non-defective modules are highly interleaved, suggesting that static metrics alone aren't a "silver bullet" for small functions.
# 2. **Outlier Impact:** Extreme values in `loc` and `v(g)` are predominantly associated with defects (orange points), confirming that high complexity is a strong indicator of risk.
# 3. **Feature Correlation:** The linear patterns between `v`, `loc`, and `e` are visible, but the spread increases with scale, justifying the need for **StandardScaler** to stabilize the model's learning process.

# %% [markdown]
# # 5. Data Preprocessing & Feature Engineering
# 
# Before training our model, we must prepare the data and derive meaningful insights from the raw metrics:
# 
# 1. **Feature Engineering**: Creating new, composite metrics to capture "Logical Density":
#     * **Complexity Density**: Ratio of Cyclomatic Complexity to LOC ($v(G) / LOC$). This identifies dense, high-risk logic in small modules.
#     * **Volume per Line**: Ratio of Halstead Volume to LOC ($V / LOC$), indicating how much information is packed into each line of code.
# 2. **Data Cleaning**: 
#     * Handling mathematical anomalies by replacing infinity values (resulting from division by zero LOC) with zeros.
#     * Ensuring dataset integrity by filling missing values (NaN) to prevent model errors.
# 3. **Feature-Target Split**: Separating independent variables (X) from the defect label (y).
# 4. **Train-Test Split**: Dividing the data (using `stratify`) to ensure the model is evaluated on a representative unseen sample.
# 5. **Feature Scaling**: Normalizing metrics using `StandardScaler` (Mean=0, Std=1) to ensure fair weight distribution across different scales.

# %%
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

train['complexity_density'] = train['v(g)'] / train['loc']
train['volume_per_line'] = train['v'] / train['loc']

train.replace([np.inf, -np.inf], np.nan, inplace=True)
train.fillna(0, inplace=True)

# 1. הפרדה ל-X ו-y (זכור שהורדנו את b)
X = train.drop('defects', axis=1)
y = train['defects']

# 2. פיצול לסט אימון וסט בדיקה (20% לבדיקה)
# השתמשנו ב-stratify=y בגלל חוסר האיזון (19% באגים)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 3. נרמול הנתונים - קריטי בגלל ההבדלים שראינו ב-Describe
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"Training set size: {X_train.shape[0]} samples")
print(f"Testing set size: {X_test.shape[0]} samples")

# %%
# המרה של המערך המנורמל חזרה ל-DataFrame כדי שיהיה נוח להסתכל
X_train_scaled_train = pd.DataFrame(X_train_scaled, columns=X.columns)

# הצגת 5 השורות הראשונות
print("--- Data After Standard Scaling (X_train_scaled) ---")
display(X_train_scaled_train.head())

# הצגת סטטיסטיקה של הנתונים המנורמלים
print("\n--- Statistics After Scaling ---")
display(X_train_scaled_train.describe().round(2))

# %% [markdown]
# ### 5.4 Visualizing the Effect of Scaling
# To verify the scaling process, we visualize the feature distributions using histograms. 
# 
# **Key Observations:**
# * **Zero-Centered:** All features are now centered at a mean of **0**. Values to the left are below average, and values to the right are above average.
# * **Uniform Variance:** Most data points now fall within the range of **-3 to +3**, ensuring that the model treats all features equally regardless of their original units (e.g., lines of code vs. Halstead volume).
# * **Outlier Preservation:** While the majority of data is centered, the "long tails" (outliers) are preserved, which is important for identifying highly complex, bug-prone modules.

# %%
# היסטוגרמות של הנתונים המנורמלים
X_train_scaled_train.hist(bins=50, figsize=(15, 10), color='skyblue', edgecolor='black')
plt.suptitle('Feature Distributions After Standardization (Centered at 0)', fontsize=16)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()

# %% [markdown]
# # 6. Model Training & Evaluation
# 
# ## 6.1 Algorithm Selection: Logistic Regression
# We selected **Logistic Regression** as our primary classification model. It is a robust and efficient algorithm for binary classification tasks, offering high interpretability which is essential for understanding how code metrics influence defect probability.
# 
# ## 6.2 Strategy for Imbalanced Data
# As identified during the EDA phase, only **19.35%** of the modules contain defects. To prevent the model from being biased toward the majority class ("No Defects"), we implemented the following strategy:
# 
# * **Class Weighting**: We utilized the `class_weight='balanced'` parameter. This penalizes the model more heavily for missing a defect than for a false alarm.
# * **Focus on Recall**: Our primary goal is to ensure the AI agent identifies as many potential bugs as possible. High **Recall** is prioritized over high Precision in this safety-critical context.

# %%
from sklearn.linear_model import LogisticRegression

# Initialize the model with balanced class weights
logmodel = LogisticRegression(class_weight='balanced', random_state=42)

# Fit the model to the scaled training data
logmodel.fit(X_train_scaled, y_train)

# Generate predictions on the scaled test set
predictions = logmodel.predict(X_test_scaled)

print("Logistic Regression Model trained and predictions generated.")

# %% [markdown]
# ## 7. Performance Analysis
# 
# To evaluate the model's effectiveness, we use a **Confusion Matrix** and a **Classification Report**. Given the class imbalance, we look beyond simple Accuracy and focus on the following metrics:
# 
# ### Key Metrics Explained:
# 1.  **Recall (Sensitivity)**: Out of all actual defects, how many did the model catch? (Crucial for bug detection).
# 2.  **Precision**: When the model predicts a defect, how often is it correct?
# 3.  **F1-Score**: The harmonic mean of Precision and Recall, providing a balanced view of the model's performance.

# %%
from sklearn.metrics import classification_report, confusion_matrix

log_importance = pd.DataFrame(index=X.columns, data=logmodel.coef_[0], columns=['Coefficient'])
print("--- Logistic Regression Coefficients ---")
print(log_importance.sort_values(by='Coefficient', ascending=False))

# # Confusion Matrix
# print("--- Confusion Matrix ---")
# print(confusion_matrix(y_test, predictions))

# # Full Report
# print("\n--- Classification Report ---")
# print(classification_report(y_test, predictions))


# 1. במקום predict, נשתמש ב-predict_proba כדי לקבל הסתברויות
# התוצאה היא מערך של [הסתברות ל-0, הסתברות ל-1]
log_probs = logmodel.predict_proba(X_test_scaled)[:, 1]
# print(f"--- log_probs {log_probs} ---")
# 2. הגדרת הסף החדש (למשל 0.3)
custom_threshold = 0.40

# 3. יצירת תחזיות חדשות: אם ההסתברות >= 0.3, זה באג (1), אחרת תקין (0)
log_final_preds = (log_probs >= custom_threshold).astype(int)

# 4. בדיקת התוצאות החדשות
from sklearn.metrics import classification_report, confusion_matrix
print(f"--- Logistic Regression with {custom_threshold} Threshold ---")
print("--- Confusion Matrix ---")
print(confusion_matrix(y_test, log_final_preds))
print(classification_report(y_test, log_final_preds))

# %% [markdown]
# # 8. Final Results & Interpretation
# 
# ---
# 
# ### 8.1 Performance Summary
# 
# Our **Logistic Regression** model was optimized for **high-recall defect detection** to ensure maximum code coverage for our Autonomous Test Agent. Using a custom probability threshold of **0.4** and **balanced class weights**, we yielded the following results for defect detection (**Class 1**):
# 
# * **Recall: 0.80** – The model successfully identified **80% of all actual defective modules**. This high sensitivity is critical for our agent, ensuring that most bug-prone areas are flagged for test generation.
# * **Precision: 0.25** – While maintaining high recall, the model produces some false positives. However, in the context of automated testing, a "False Positive" often identifies complex code that still benefits from test coverage.
# * **F1-Score: 0.38** – Represents the strategic balance between our ability to catch bugs and the frequency of false alarms, prioritizing safety and coverage.
# 
# ---
# 
# ### 8.2 Conclusion
# 
# The model demonstrates a robust ability to prioritize code modules for automated testing, significantly outperforming a random guess. By integrating advanced metrics like **Complexity Density** and **Volume per Line** (derived from **Radon**), the system moves beyond simple line-counting to a more nuanced understanding of software risk.
# 
# #### **Key Takeaways for the Autonomous Agent:**
# 1.  **Strategic Coverage:** Achieving **80% recall** provides a strong safety net for the development pipeline, ensuring that the autonomous agent focuses its resources where defects are most likely to hide.
# 2.  **Feature Synergy:** The combination of traditional software metrics with modern **logical density analysis** (Radon-based) proved effective in identifying bug-prone patterns.
# 3.  **Autonomous Decision Making:** This model serves as the **decision-making engine** of our Multi-Agent System, allowing the agent to make data-driven decisions on where to allocate compute resources for test generation.
# 
# ### 8.3 Next Steps for Improvement
# 
# To further refine the agent's decision-making capabilities, the following steps are proposed:
# 
# 1. **Model Evolution**: 
#    * Moving beyond linear boundaries by implementing **Ensemble Methods** such as **Random Forest** or **XGBoost**. These models are better equipped to capture non-linear relationships between code density and defect probability.
# 
# 2. **Dynamic Threshold Optimization**: 
#    * Implementing an **adaptive threshold** that adjusts based on the "Risk Profile" of a project. For mission-critical modules, the system could automatically lower the threshold to maximize Recall, while using a more conservative setting for secondary scripts.
# 
# 3. **Cross-Language Validation**: 
#    * Testing and calibrating the model on diverse datasets beyond Python (e.g., Java or C# datasets from the Promise repository) to ensure the agent's predictive logic is language-agnostic.

# %% [markdown]
# # 9. Model Upgrade: Random Forest Classifier
# 
# ## 9.1 Why Random Forest?
# After evaluating the **Logistic Regression** baseline, we observed that while it captures general trends, it struggles with the non-linear distribution and high overlap in software metrics. To achieve better performance, we transition to **Random Forest**, an ensemble learning method that offers several advantages:
# 
# * **Non-Linear Decision Boundaries**: Unlike Logistic Regression, Random Forest uses multiple decision trees to capture complex "pockets" of defects that don't follow a straight linear line.
# * **Feature Interaction**: It inherently identifies how combinations of metrics (e.g., how high `loc` combined with high `complexity_density`) increase bug probability.
# * **Robustness to Outliers**: Decision trees are less sensitive to the extreme outliers we observed in metrics like `Effort (e)` and `Volume (v)`.

# %%
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# 1. Initialize Random Forest with balanced weights
# rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
# rf_model = RandomForestClassifier(n_estimators=800, max_depth=20, min_samples_leaf=8, max_features='log2')
# rf_model = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
rf_model = RandomForestClassifier(
    n_estimators=800, 
    max_depth=20, 
    class_weight='balanced', # חובה ל-Recall גבוה!
    random_state=42
)

# 2. Train the model
rf_model.fit(X_train_scaled, y_train)

rf_importance = pd.DataFrame(index=X.columns, data=rf_model.feature_importances_, columns=['Importance'])
print("\n--- Random Forest Feature Importance ---")
print(rf_importance.sort_values(by='Importance', ascending=False))


# 3. Predict
rf_predictions = rf_model.predict(X_test_scaled)

# 4. Evaluate
print("--- Random Forest Confusion Matrix ---")
print(confusion_matrix(y_test, rf_predictions))
print("\n--- Random Forest Classification Report ---")
print(classification_report(y_test, rf_predictions))

# %% [markdown]
# ## 9.2 Optimization for the Autonomous Agent (Threshold Tuning)
# While the Random Forest model with balanced weights improves overall stability, a standard **0.5 threshold** is often too conservative for our agent's specific mission. 
# 
# In the context of our **Autonomous Test Agent**, the cost of a **False Negative** (missing a bug and leaving code untested) is significantly higher than the cost of a **False Positive** (generating an extra, unnecessary test). To prioritize **Recall** and ensure maximum safety, we implemented a **Custom Probability Threshold of 0.2**.
# 
# This adjustment allows the agent to be more "vigilant," flagging modules for testing even when the model has lower confidence, thus providing a stronger safety net for the codebase.

# %%
# קבלת ההסתברויות (Probabilities)
# print("--- X_test_scaled ---", X_test_scaled)
# rf_probs = rf_model.predict_proba(X_test_scaled)
# print("--- rf_probs ---", rf_probs)

# קבלת ההסתברויות (Probabilities)
rf_probs = rf_model.predict_proba(X_test_scaled)[:, 1]

# הגדרת סף נמוך יותר - מספיק ש-30% מהעצים יחשדו בבאג
custom_threshold = 0.2
rf_final_preds = (rf_probs >= custom_threshold).astype(int)

print("--- Random Forest with 0.2 Threshold ---")
print(classification_report(y_test, rf_final_preds))

# %% [markdown]
# ## 9.3 Interpretation & Feature Importance
# Beyond raw predictive power, Random Forest provides **Feature Importance** scores. This is a critical component of our system's **Explainable AI (XAI)** capability. 
# 
# By analyzing which metrics (such as `complexity_density` or `volume_per_line`) most influenced the prediction, the Multi-Agent system can provide reasoning for its actions. Instead of a "black-box" decision, the agent can justify its choice to write a test based on the specific structural risks identified by the **Radon** metrics.

# %% [markdown]
# # 10. Model Export for Deployment

# %%
import pickle

# שמירת המודל
with open('bug_prediction_model.pkl', 'wb') as f:
    pickle.dump(rf_model, f)

# שמירת הסקלר (קריטי! כי המודל חייב לקבל נתונים מנורמלים באותה צורה)
with open('scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)


