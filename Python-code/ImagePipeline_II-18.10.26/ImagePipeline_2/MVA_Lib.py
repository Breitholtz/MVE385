# -*- coding: utf-8 -*-
import os
import numpy as np
import numpy.linalg as linalg
import scipy
import sklearn.decomposition

import matplotlib.pyplot as plt


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

    
def getNpIndices( booleanArray ):
    indices = np.where(booleanArray==True)[0]
    return indices    


def print_shape_and_type( A ):
    print( A.shape, A.dtype)

#def ScaleAndCenter( Xin, Xws, Xavg ):
#
#    OnesCol =  np.mat( np.ones( (objects, 1) ))
#    X_wgt_mat = OnesCol * Xws
#    X = np.multiply( Xin, X_wgt_mat )
#    # X = np.divide( Xin, X_wgt_mat )
#    X_Cent_mat = OnesCol * Xavg
#    X = np.mat(X - X_Cent_mat)
#    return X 

"""Make new model ---------------------------------------------------------"""
def center(X0):
    if X0.ndim == 1:
        X = np.mat(X0).T
    else:
        X = X0        
    centrum = np.mat(X.mean(axis=0))
    one_col = np.mat(np.ones_like(X[:,0]))
#    print('center', one_col.shape, centrum.shape, X.shape)
    centered = X - np.outer(one_col,centrum)
    return centered, centrum
    
def UV_scale(X):
    py_std = np.mat(X.std(axis=0, ddof=1)) 
                    #N.B. ddof =1 is equal to division by N-1, where ddof is Delta Degrees of Freedom 
    one_col = np.mat(np.ones_like(X[:,0]))
    scalers = 1/py_std
    print('UV_scale', one_col.shape, py_std.shape, X.shape)
    scaled_X = np.multiply( X, np.outer(one_col, scalers))
    # print 'scalers ', scalers
    return scaled_X, scalers
    
def normalize( p ):
    # print p
    return p/(np.sqrt(p * p.T))
    
def PCA_part( X_part, p):
    t = X_part * p.T
    # print 'paraPCA_part t ', t
    p_out2 = t.T * X_part
    return p_out2
    
    
def PCA_iter(X):
    rows, cols = X.shape
    p_start = np.mat(np.ones((1,cols), float))
    p = normalize(p_start)
    sin_angle = 1.0
    limit = 1.0E-6
    n = 0
    # print 'X.shape: ', X.shape
    while sin_angle > limit:
        p_out = PCA_part(X, p)
        # print( 'p_out ', p_out)
        p_out = normalize(p_out)
        sin_angle = 1.0 - abs(p * p_out.T)
        n = n+1
##        print( "   Iteration: ", n, sin_angle)
        p = p_out
    t = X * p.T
    E = X - t*p_out
    print( n, ' iterations, final sin_angle: ', sin_angle)
    return p_out, t, E

def PCA_comp( E, components ):
    if components > 0:
        P, T, E = PCA_iter(E)
        for i in range(2,components+1):
            print( 'Enter component ', i)
            p, t, E = PCA_iter(E)
            P = np.vstack((P,p))
            T = np.hstack((T,t))
        return P, T, E
    

def PCA_by_SVD(X, components):
    trace = True
    U, S, V = scipy.linalg.svd(X, full_matrices=False)        
    T = U[:,0:components]*S[0:components]
    P = V[0:components,:]
    if trace:
        print()
        print('SVD U S shapes', U.shape, S.shape )
        print('PCA T.shape', T.shape)
    return T, P, S

def PCA_by_randomizedSVD(X, components):
    trace = True
    U, S, V = sklearn.decomposition.randomized_svd(X, components)        
    T = U*S
    P = V
    if trace:
        print()
        print('randomized SVD U S shapes', U.shape, S.shape )
        print('PCA T.shape', T.shape)
    return T, P, S


def PCA_by_SVD_DModX(X, P, components):
    T_pred = np.mat(X) * np.mat(P[0:components, :].T)
#    T_pred = X @ P[0:components, :].T
    X_mod = T_pred * P[0:components, :]
    X_resid = X - X_mod
    DModX = np.std(X_resid, axis=1, ddof=1)
    return DModX

def NMF(X, components):
    Xmin = np.min(X)
    Xpos = X - Xmin # adjust if zero is not lowest value
    NMF_decomp = sklearn.decomposition.NMF(n_components=components, random_state=1)
    T = NMF_decomp.fit_transform(Xpos)
    P = NMF_decomp.components_
    return T, P
    

"""Prediction -------------------------------------------------------------"""

def CenterAndScale( Xin, Xws, Xavg ):
    """Combined center and UV scaling in the same order as in Simca
       when the weights (Xws), and averages (Avg) are already defined"""
    objects, vars = Xin.shape
    OnesCol =  np.mat( np.ones( (objects, 1) ))
    X_Cent_mat = OnesCol * Xavg
    print( 'Xin ',end=' ')
    print_shape_and_type( Xin )
    print( 'X_Cent_mat ',end=' ')
    print_shape_and_type( X_Cent_mat )
    X = np.mat(Xin - X_Cent_mat)
    X_wgt_mat = OnesCol * Xws
    X = np.multiply( X, X_wgt_mat )
    return X

def logit( X, C1, C2 ):
    # print X
    y = np.log10(np.divide(( X-C1 ), ( C2-X )))    
    return y

def inv_logit( X0, C1, C2 ):
    X = np.asarray(X0)
    y = np.divide(C2*10**X + C1, 1 + 10**X)
    return y

def GetVectorIndices( ListID, VectorName ):
    index = 0
    out_index = []
    for ID in ListID:
        entry =  ID.replace('[', '.')
        entry =  entry .replace('[', '.')
        entry =  entry .replace('(', '.')
        splitted = entry.split( '.')
        # print splitted[1].rstrip(), len(splitted[1].rstrip())
        if splitted[1].rstrip() == VectorName: 
           out_index.append( index )
        index = index + 1
    return out_index 
        

def GetModelMatrix( matfile, VectorName):
    indices = GetVectorIndices( matfile['VARID1'], VectorName )
    OutMat = np.mat(matfile['DATA'][:,indices]).T
    # print indices, matfile['VARID1'][indices], OutMat.shape
    return OutMat
    
    
def GetModelName( matfile ):
    ListID = matfile['VARID1'][0]
    entry =  ListID.replace('[', '.')
    entry =  entry .replace('[', '.')
    splitted = entry.split( '.') 
    return splitted[0] # 1st part in VARID1 names contain the model name 

    
def GetModelMaxComponents( matfile ):
    P = GetModelMatrix( matfile, 'p')
    components, variables = P.shape
    return components

def GetModelVarIDs( matfile ):
    print('GetModelVarIDs', matfile['OBSID1'][0], type(matfile['OBSID1'][0][0]))
    if isinstance(matfile['OBSID1'][0][0], np.float64):
        VarIDs = []
        num_VarIDs = np.squeeze(np.asarray(matfile['OBSID1']))
        for num_VarID in num_VarIDs:
            VarIDs.append(str(num_VarID))
    else:            
        VarIDs = list(matfile['OBSID1']) # Variable IDs from a model are in a column when taken from an exported Simca-P list
    NumericVarIDs = matfile['OBSID2']
    return VarIDs, NumericVarIDs

def AppendMat( Mat, column ):
    if Mat is None:
        Mat = column
    else:
        Mat = np.hstack((Mat, column))
    return Mat

# In python 2.6 and Kubuntu 10.10 the X_fileName is not recognised
# when moved into a secondary file for subroutines
def OpenModel0( X_fileName, Y_fileName ):
    X_matfile = scipy.io.loadmat( X_filename )
    Xavg = GetModelMatrix( X_matfile, 'Xavg')
    Xws = GetModelMatrix( X_matfile, 'Xws')
    P = GetModelMatrix( X_matfile, 'p')
    W = GetModelMatrix( X_matfile, 'w')
    a = GetModelMaxComponents( X_matfile )

    Y_matfile = scipy.io.loadmat( Y_filename )
    Yavg = GetModelMatrix( Y_matfile, 'Yavg')
    Yws = GetModelMatrix( Y_matfile, 'Yws')
    C = GetModelMatrix( Y_matfile, 'c')
    ModelName = GetModelName( X_matfile )
    return Xavg, Xws, P, W, a, Yavg, Yws, C, ModelName

def Open_X_model( X_matfile ):
    X_model = {}
    X_model['Xavg'] = GetModelMatrix( X_matfile, 'Xavg')
    X_model['Xws'] = GetModelMatrix( X_matfile, 'Xws')
    X_model['P'] = GetModelMatrix( X_matfile, 'p')
    X_model['W']= GetModelMatrix( X_matfile, 'w')
    X_model['components'] = GetModelMaxComponents( X_matfile )
    X_model['XObs'] = GetModelMatrix( X_matfile, 'XObs')
    X_model['ModelName'] = GetModelName( X_matfile )
    return X_model
    
def Open_Y_model( Y_matfile ):
    Y_model = {}
    Y_model['Yavg'] = GetModelMatrix( Y_matfile, 'Yavg')
    Y_model['Yws'] = GetModelMatrix( Y_matfile, 'Yws')
    Y_model['C'] = GetModelMatrix( Y_matfile, 'c')
    Y_model['ModelName'] = GetModelName( Y_matfile )
    return Y_model

def OpenModel( X_matfile, Y_matfile ):
    # X_matfile = scipy.io.loadmat( X_filename )
    Xavg = GetModelMatrix( X_matfile, 'Xavg')
    Xws = GetModelMatrix( X_matfile, 'Xws')
    P = GetModelMatrix( X_matfile, 'p')
    W = GetModelMatrix( X_matfile, 'w')
    a = GetModelMaxComponents( X_matfile )
    XObs = GetModelMatrix( X_matfile, 'XObs')

    # Y_matfile = scipy.io.loadmat( Y_filename )
    Yavg = GetModelMatrix( Y_matfile, 'Yavg')
    Yws = GetModelMatrix( Y_matfile, 'Yws')
    C = GetModelMatrix( Y_matfile, 'c')
    ModelName = GetModelName( X_matfile )
    return Xavg, Xws, P, W, a, Yavg, Yws, C, ModelName

def MatchModelVars( Model, Xdata ):
    pass
    
def PLSpredict( Xin, Xavg, Xws, P, W, a, Yavg, Yws, C ):
    objects, vars = Xin.shape
    
##    X = CenterAndScale( Xin, Xws, Xavg )
##    E = X.copy()
    E = CenterAndScale( Xin, Xws, Xavg )
    OnesCol =  np.mat( np.ones( (objects, 1) ))
    # Y = OnesCol * Yavg
    T = None
    for i in range(0, a):
        print( 'PLS component: ', i)
        t = E * W[ i, : ].T
        E = E - t * P[ i, : ]
        # Y = Y + t * C[ i, : ]
        T = AppendMat( T, t )
        # print 'LoopCount ', i
        
    Ynosubt = OnesCol * Yavg + np.divide(T*C, OnesCol * Yws)
    return Ynosubt, T, E

def PLSpredictTrans( Xin, Xavg, Xws, P, W, a, Yavg, Yws, C ):
    objects, vars = Xin.shape
    
    X = CenterAndScale( Xin, Xws, Xavg )
    E = X.copy()
    OnesCol =  np.mat( np.ones( (objects, 1) ))
    # Y = OnesCol * Yavg
    T = None
    for i in range(0, a):
        t = E * W[ i, : ].T
        E = E - t * P[ i, : ]
        # Y = Y + t * C[ i, : ]
        T = AppendMat( T, t )
        # print 'LoopCount ', iTest_XObs_against_workset_2( XObs, Xavg, Xws, Workset ):
    Y_non_avg = T*C
    Ytot = OnesCol * Yavg + Y_non_avg
    TransformedY = Ytot
    TransformedY[:,2] = logit(Ytot[:,2], 0, 110)    
    Ynosubt = np.divide(TransformedY, OnesCol * Yws)
    return Ynosubt, T, E

def PLScoeffsPredict( Xin, Xavg, Xws, P, W, a, Yavg, Yws, C ):

    Coeffs = W.T*linalg.inv(P*W.T)*C #[:,0]
    # print 'linalg.inv(P*W.T).bud 5v M3 PLS-DA_X_w_XObs.matshape ', linalg.inv(P*W.T).shape
    X = CenterAndScale( Xin, Xws, Xavg )
    objects, vars = Xin.shape
    OnesCol =  np.mat( np.ones( (objects, 1) ))
    Y = OnesCol * Yavg + np.divide(X*Coeffs, OnesCol * Yws)
    return Y, T, E

def PLSpredictFromLoop( Xin, Xavg, Xws, P, W, a, Yavg, Yws, C ):
    objects, vars = Xin.shape
    X = CenterAndScale( Xin, Xws, Xavg )
    E = X.copy()
    OnesCol =  np.mat( np.ones( (objects, 1) ))
    Y = OnesCol * Yavg
    # Should be Y = OnesCol * np.zeros(Yavg)
    T = None
    for i in range(0, a):
        t = E * W[ i, : ].T
        E = E - t * P[ i, : ]
        Y = Y + t * C[ i, : ]
        T = AppendMat( T, t )
        # print 'LoopCount ', i
    
    Yout = np.divide( Y, OnesCol * Yws )
    # Should be Yout = OnesCol * Yavg + np.divide( Y, OnesCol * Yws )
     
    return Yout, T, E

def Test_against_workset( TrainingSetX, WS, Xws, Xavg ):
    
    Xmodel = CenterAndScale( TrainingSetX, Xws, Xavg )
    RelDiff = abs(np.divide( Xmodel-WS, WS)*1000000)
    MeanRelDiff = RelDiff.mean(axis=0)
    # print RelDiff
    print( MeanRelDiff)
    fig1 = plt.figure()
    ax = fig1.add_subplot(111)
    ax.plot(MeanRelDiff.T)
    plt.ylabel('ppm')
    plt.title( 'Test X against workset')
    
def Get_XObs( X_matfile ):
    XObs = GetModelMatrix( X_matfile, 'XObs')
    return XObs

def Get_workset( Xavg, WorksetMatfile ):

    dummy, num_X_variables = Xavg.shape
    Workset = {}
    Workset['X'] = WorksetMatfile['DATA'][:,0:num_X_variables]
    Workset['Y'] = WorksetMatfile['DATA'][:,num_X_variables-1:-1]
    # print "Workset['X'].shape, Workset['Y'].shape ", Workset['X'].shape, Workset['Y'].shape
    return Workset

def Test_XObs_against_workset_2( XObs, Xavg, Xws, Workset_X ): # This version takes the workset from a dictionary
    
    num_X_variables = Xavg.shape[1] 
    WS = Workset_X
    Xmodel = CenterAndScale( XObs, Xws, Xavg )
    RelDiff = abs(np.divide( Xmodel-WS, WS)*1000000)
    MeanRelDiff = RelDiff.mean(axis=0)
    # print RelDiff
    # print MeanRelDiff
    fig1 = plt.figure()
    ax = fig1.add_subplot(111)
    ax.plot(np.arange(1, num_X_variables+1), MeanRelDiff.T)
    plt.ylabel('ppm')
    plt.xlabel('variable number')
    plt.title( 'Test XObs against workset')
    plt.show()
    
def Test_XObs_against_workset( XObs, Xavg, Xws, WorksetMatfile ): # This version takes the workset from a file
    
    dummy, num_X_variables = Xavg.shape
    WS = WorksetMatfile['DATA'][:,0:num_X_variables]
    Xmodel = CenterAndScale( XObs, Xws, Xavg )
    RelDiff = abs(np.divide( Xmodel-WS, WS)*1000000)
    MeanRelDiff = RelDiff.mean(axis=0)
    # print RelDiff
    # print MeanRelDiff
    fig1 = plt.figure()
    ax = fig1.add_subplot(111)
    ax.plot(np.arange(1, num_X_variables+1), MeanRelDiff.T)
    plt.ylabel('ppm')
    plt.xlabel('variable number')
    plt.title( 'Test XObs against workset') 
    plt.show()



if __name__ == '__main__':
        
    print( '"MVA_Lib.py" is not the main program')