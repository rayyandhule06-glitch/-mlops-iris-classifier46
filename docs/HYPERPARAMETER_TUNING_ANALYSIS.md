# Hyperparameter Tuning Analysis

## 1. Baseline Model

Model:

DecisionTreeClassifier

CV F1 Macro:

0.9663

Test Accuracy:

0.9000

The baseline Decision Tree was used as a reference model before applying hyperparameter tuning.

## 2. Grid Search

Model:

RandomForestClassifier

Total combinations:

72

Cross-validation:

5-fold

Total fits:

360

Best CV F1 Macro:

0.9663

Test Accuracy:

0.9667

Best Parameters:

- max_depth = 3
- max_features = sqrt
- min_samples_split = 2
- n_estimators = 50

Grid Search exhaustively evaluated all combinations in the specified hyperparameter grid.

## 3. Random Search

Model:

RandomForestClassifier

Number of iterations:

30

Cross-validation:

5-fold

Total fits:

150

Best CV F1 Macro:

0.9663

Test Accuracy:

0.9667

Best Parameters:

- max_depth = 3
- max_features = sqrt
- min_samples_split = 6
- n_estimators = 100

Random Search evaluated 30 selected combinations from the defined search space.

## 4. Comparison

The baseline Decision Tree achieved a test accuracy of 0.9000.

Both Grid Search and Random Search improved the test accuracy to 0.9667.

The CV F1 Macro was 0.9663 for all three approaches.

Grid Search required 360 model fits, while Random Search required only 150 model fits.

Therefore, in this experiment, Random Search achieved the same CV F1 Macro and test accuracy as Grid Search while using significantly fewer model fits.

Grid Search is exhaustive and evaluates every combination in the specified grid, whereas Random Search evaluates a selected number of combinations from the search space.

Overall, Random Search was more computationally efficient in this experiment while achieving the same performance as Grid Search.