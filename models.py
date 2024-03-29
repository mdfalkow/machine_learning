import math
import random
from time import time

import numpy as np

from typing import Callable


class BaseModel(object):
    """
    BaseModel class definition. All models inherit from this class.

    Attributes
    ----------
    X : numpy.ndarray (2 dimensional)
        Matrix containing data used to build the model.
    y : numpy.ndarray (1 dimensional)
        Vector containing labels for data points in X.
    feat_trans: Callable[numpy.ndarray]
        Feature transformation function on an individual point. 
    """

    def __init__(self, X, y, feat_trans=None):
        """
        Create a new BaseModel.

        Parameters
        ----------
        X : numpy.ndarray (2 dimensional)
            Matrix containing data used to build the model.
        y : numpy.ndarray (1 dimensional)
            Vector containing labels for data points in X.
        feat_trans: Callable[[numpy.ndarray], numpy.ndarray], optional
            Feature transformation function on an individual point.
            (Default: None, implies no feature transformation)

        Raises
        ------
        ValueError
            - If argument dimensions do not match.
            - If X is not 2 dimensional.
            - If y is not 1 dimensional.
            - If feature transformation fails.
            - If the first column of X is a dummy feature. *WIP*
        """
        X = np.array(X, dtype='float')
        y = np.array(y, dtype='float')

        if len(X.shape) != 2:
            raise ValueError(
                f'{X.shape} is invalid shape for X. Should be 2-dimensional.')
        if len(y.shape) != 1:
            raise ValueError(
                f'{y.shape} is invalid shape for y. Should be 1-dimensional.')
        if len(X) != len(y):
            raise ValueError(
                f'Unequal dimensions. len(X) ({len(X)}) != len(y) ({len(y)})')

        if feat_trans != None:
            try:
                X = np.array([feat_trans(x) for x in X], dtype='float')
            except e:
                raise ValueError(f'Feature transform failed\n{e}')

        self.X = X
        self.y = y
        self.feat_trans = feat_trans


class LinearModel(BaseModel):
    """
    Implementation of the linear model for classification.

    Attributes
    ----------
    X : numpy.ndarray (2 dimensional)
        Matrix containing data used to build the model.
    y : numpy.ndarray (1 dimensional)
        Vector containing labels for data points in X.
    feat_trans: Callable[[numpy.ndarray], numpy.ndarray]
        Feature transformation function on an individual point.
    w : numpy.ndarray
        Weight vector of the model.
    r : float
        Regularization coefficient for the model.
    """

    def __init__(self,
                 X: np.ndarray,
                 y: np.ndarray,
                 r: float = 0,
                 feat_trans: Callable[[numpy.ndarray], numpy.ndarray] = None,
                 n_iter: int = 2000,
                 debug: bool = False):
        """
        Create a new LinearModel.

        Parameters
        ----------
        X : numpy.ndarray (2 dimensional)
            Matrix containing the training data. 
        y : numpy.ndarray (1 dimensional)
            Labels for training data.
        r : float, optional
            Regularization coefficient (Default: 0).
        feat_trans: Callable[[numpy.ndarray], numpy.ndarray], optional
            Feature transformation function on an individual point.
            (Default: None)
        n_iter : int, optional
            Number of training iterations (Default: 2000).
        debug : bool, optional
            Prints out training information if True (default: False).

        Raises
        ------
        ValueError
            If conditions for BaseModel are not met.
        """
        super().__init__(X, y, feat_trans)

        self.X = np.asfarray(np.column_stack(
            (np.ones_like(self.X.shape[0]), self.X)))
        self.r = r

        self._debug = debug
        self._n_iter = n_iter

        self.w = self._train_model()

    def _train_model(self) -> np.ndarray:
        """
        Train model on provided data using Linear regression then pocket
        perceptron learning algorithm for improvement.

        Returns
        -------
        numpy.ndarray
            The weight vector resulting from training.
        """
        w_ = self._calc_w_lin()
        E_ = self._calc_E_in(w_)

        @staticmethod
        def debug(t):
            print(f'{time()} | iter: {t} | (E_, w_): {E_, w_}')

        w = np.copy(self.w)
        for t in range(n_iter):
            if debug:
                debug(t)
            while True:
                # pick random point and classify
                i = random.randint(0, len(self.X) - 1)
                if self._classify(self.X[i], w) != self.y[i]:
                    # Update w and E_in
                    w += self.y[i] * self.X[i]
                    E_in = self._calc_E_in(w)
                    if E_in < E_:
                        E_ = E_in
                        np.copyto(w_, w)
                    break
        if debug:
            debug(self._n_iter)

        return w_

    def _calc_w_lin(self) -> np.ndarray:
        """
        Calculate w_lin, the weight vector from linear regression.

        Returns
        -------
        numpy.ndarray
            The weight vector from determined by linear regression.
        """
        n = self.X.shape[1]
        return (np.linalg.inv((self.X.T @ self.X) +
                               self.r * np.eye(n)) @ self.X.T) @ self.y

    def _calc_E_in(self, w: np.ndarray = None) -> float:
        """
        Calculate in-sample error for specified weight vector.

        Parameters
        ----------
        w : numpy.ndarray, optional
            Weight vector for calculating E_in
            (Default: None, uses model's weight vector)

        Returns
        -------
        float
            In-sample error, E_in, for the provided weight vector.
        """
        w = w if w != None else self.w
        pred = self.X @ w
        pred[pred >= 0] = 1
        pred[pred < 0] = -1
        return np.sum(np.abs(pred - self.y) / 2) + self.r * (w @ w)

    def _classify(self, x, w) -> int:
        """
        Classifies x using the weight vector w.
        Assumes x has already gone through feature transformation.

        Parameters
        ----------
        x : numpy.ndarray
            Point to classify
        w : numpy.ndarray, optional
            Weight vector to use for classification
            (Default: None, uses model's weight vector)

        Returns
        -------
        int
             1 if `np.dot(x, w)` >= 0; -1 otherwise.
        """
        return 1 if np.dot(x, w) >= 0 else -1

    def classify(self, x: np.ndarray, w: np.ndarray = None) -> int:
        """
        Classifies x using the weight vector w.
        Will perform feature transformation on x if self.feat_trans != None.

        Parameters
        ----------
        x : numpy.ndarray
            Point to classify
        w : numpy.ndarray, optional
            Weight vector to use for classification
            (Default: None, uses model's weight vector)

        Raises
        ------
        ValueError
            If feature transformation fails.

        Returns
        -------
        int
             1 if `np.dot(x, w)` >= 0; -1 otherwise.
        """
        # feature transformation
        if self.feat_trans != None:
            try:
                x = self.feat_trans(x)
            except e:
                raise ValueError(f'Feature transform failed\n{e}')
        return self._classify(x, w)

    def classify_all(self, X: np.ndarray, w: np.ndarray = None):
        """
        Classify a collection of points.

        Parameters
        ----------
        X : numpy.ndarray
            Points to classify
        w : numpy.ndarray, optional
            Weight vector for calculating E_in
            (Default: None, uses model's weight vector)

        Raises
        ------
        ValueError
            If feature transformation fails.

        Returns
        -------
        numpy.ndarray
            Predicted labels for the points in X
        """
        w = w if w != None else self.w
        if self.feat_trans != None:
            try:
                X = np.array([self.feat_trans(x) for x in X])
            except e:
                raise ValueError(f'Feature transform failed\n{e}')

        pred = X @ w
        pred[pred >= 0] = 1
        pred[pred < 0] = -1
        return pred


class kNNModel(BaseModel):
    """
    Implementation of the k-Nearest Neighbors model for classification.

    Attributes
    ----------
    X : numpy.ndarray (2 dimensional)
        Matrix containing data used to build the model.
    y : numpy.ndarray (1 dimensional)
        Vector containing labels for data points in X.
    feat_trans: Callable[[numpy.ndarray], numpy.ndarray]
        Feature transformation function on an individual point.
    k : int
        Number of nearest neighbors to check.
    """

    def __init__(self, X: np.ndarray, y: np.ndarray, k: int = 1):
        """
        Create a new kNNModel

        Parameters
        ----------
        X : numpy.ndarray (2 dimensional)
            Matrix containing data used to build the model.
        y : numpy.ndarray (1 dimensional)
            Vector containing labels for data points in X.
        k : int, optional
            Number of nearest neighbors to check (Default : 1)

        Raises
        ------
        ValueError
            If conditions for BaseModel are not met.
        """
        super().__init__(X, y)
        self.k = k

    @staticmethod
    def _euclidean_distance(x1: np.ndarray, x2: np.ndarray) -> float:
        """
        Returns distance between two points.

        Parameters
        ----------
        x1 : numpy.ndarray
            First point.
        x2 : numpy.ndarray
            Second point.

        Returns
        -------
        float
            Euclidean distance between x1 and x2.
        """
        return np.linalg.norm(x1 - x2)

    def classify(self, x: np.ndarray, k: int = None) -> int:
        """
        Classify a point based on the k-nearest neighbors.

        Parameters
        ----------
        x : numpy.ndarray
            Point to classify.
        k : int, optional
            Number of nearest neighbors to check.
            (Default: None, uses model's k attribute).

        Raises
        ------
        ValueError
            If feature transformation fails.

        Returns
        -------
        int
             1 if the k-nearest neighbors have labels >= 0; -1 otherwise.
        """
        # use provided, otherwise use default
        k = k if k != None else self.k

        # feature transformation
        if self.feat_trans != None:
            try:
                x = self.feat_trans(x)
            except e:
                raise ValueError(f'Feature transform failed\n{e}')

        # get distance to each point in X, then sort
        distances = sorted((self._euclidean_distance(x, self.X[i]), self.y[i])
                           for i in range(len(self.X)))

        # get k nearest neighbors, then take the sum of the labels
        nearest_neighbors = distances[:k]
        return 1 if sum(label for _, label in nearest_neighbors) >= 0 else -1

    def classify_all(self, X: np.ndarray, k: int = None):
        """
        Classify a collection point based on their k-nearest neighbors.

        Parameters
        ----------
        X : numpy.ndarray (2-dimensional)
            Dataset to classify.
        k : int, optional
            Number of nearest neighbors to check.
            (Default: None, uses model's k attribute).

        Returns
        -------
        numpy.ndarray
            Array of labels corresponding to the points in X_
        """
        # use provided, otherwise use default
        k = k if k != None else self.k

        # classify all and return
        return np.array([self.classify(x, k) for x in X])

    def classification_error(self, X: np.ndarray, y: np.ndarray, k: int = None):
        """
        Classify a collection point based on their k-nearest neighbors.

        Parameters
        ----------
        X : numpy.ndarray (2-dimensional)
            Dataset to classify.
        y : numpy.ndarray (1-dimensional)
            Expected labels for X.
        k : int, optional
            Number of nearest neighbors to check.
            (Default: None, uses model's k attribute).

        Returns
        -------
        float:
            Total classification error by the model for the points in X
        """
        # use provided, otherwise use default
        k = k if k != None else self.k

        # classify all points
        predictions = self.classify_all(X, k)
        return np.sum(np.abs(predictions - y)/2) / len(y)


class RBFModel(BaseModel):
    """
    Implementation of the linear model for classification.

    Attributes
    ----------
    X : numpy.ndarray (2 dimensional)
        Matrix containing data used to build the model.
    y : numpy.ndarray (1 dimensional)
        Vector containing labels for data points in X.
    Mu : numpy.ndarray (2 dimensional)
        Centers of the data
    feat_trans: Callable[[numpy.ndarray], numpy.ndarray]
        Feature transformation function on an individual point.
    kernel_func: Callable[[float], float]
        Kernel Function to be used in feature_transformation
    w : numpy.ndarray
        Weight vector of the model.
    r : float
        Scaling constant
    """

    def __init__(self,
                 X: np.ndarray,
                 y: np.ndarray,
                 Mu: np.ndarray,
                 kern: Callable[[float], float] = None,
                 r: float = 2):
        """
        Create a new RBFModel.

        Parameters
        ----------
        X : numpy.ndarray (2 dimensional)
            Matrix containing the training data.
        y : numpy.ndarray (1 dimensional)
            Labels for training data.
        Mu : numpy.ndarray (2 dimensional)
            Centers of the data
        kern : Callable[[float], float]
            Kernel Function used in the feature transform (default: Gaussian).
        r : float, optional
            scaling constant (default: 2).
        debug : bool, optional
            Prints out training information if True (default: False).

        Raises
        ------
        ValueError
            If conditions for BaseModel are not met.
        """
        super().__init__(X, y)
        self.kern = kern if kern != None else self._gaussian_kernel
        self.Mu = Mu
        self.r = r
        self.feat_trans = self._feat_trans
        self.X = np.array([self.feat_trans(x) for x in X])
        self.w = self._calc_w_lin()

    def _calc_w_lin(self) -> np.ndarray:
        """
        Calculate w_lin, the weight vector from linear regression.

        Returns
        -------
        numpy.ndarray
            The weight vector from determined by linear regression.
        """
        return (np.linalg.inv(self.X.T @ self.X) @ self.X.T) @ self.y

    def _feat_trans(self, x: np.ndarray):
        """
        RBF feature transformation function.

        Parameters
        ----------
        x : numpy.ndarray (1 dimensional)
            Point to transform.
        Mu : numpy.ndarray (2 dimensional)
            Centers of the data.
        kern : Callable[[float], float]
            Kernel function of the RBF.
        r : float, optional
            scaling constant (default: 2).

        Returns
        -------
        numpy.ndarray
            The feature-transformed version of x.
        """
        z = [1]
        for i in range(len(self.Mu)):
            z.append(self.kern(np.linalg.norm(x - self.Mu[i])/self.r))
        return np.array(z)

    @staticmethod
    def _gaussian_kernel(z: float) -> float:
        return math.exp((-1/2) * z**2)

    def classify_all(self, X: np.ndarray):
        """
        Classify a collection of points.

        Parameters
        ----------
        X : numpy.ndarray
            Points to classify

        Raises
        ------
        ValueError
            If feature transformation fails.

        Returns
        -------
        numpy.ndarray
            Predicted labels for the points in X using weight vector w
        """
        if self.feat_trans != None:
            try:
                X = np.array([self.feat_trans(x) for x in X])
            except e:
                raise ValueError(f'Feature transform failed\n{e}')

        pred = X @ self.w
        pred[pred >= 0] = 1
        pred[pred < 0] = -1
        return pred
