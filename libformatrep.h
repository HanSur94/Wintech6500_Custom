/*
 * MATLAB Compiler: 8.0 (R2020a)
 * Date: Sat Jun  6 17:17:11 2020
 * Arguments:
 * "-B""macro_default""-W""lib:libformatrep""-T""link:lib""-d""/Users/hannessuhr
 * /Documents/OneDrive -
 * bwedu/Persönlich/Programmierung/MATLAB/RLE/libformatrep/for_testing""-v""/U
 * sers/hannessuhr/Documents/OneDrive -
 * bwedu/Persönlich/Programmierung/MATLAB/RLE/formatrep.m"
 */

#ifndef libformatrep_h
#define libformatrep_h 1

#if defined(__cplusplus) && !defined(mclmcrrt_h) && defined(__linux__)
#  pragma implementation "mclmcrrt.h"
#endif
#include "mclmcrrt.h"
#ifdef __cplusplus
extern "C" { // sbcheck:ok:extern_c
#endif

/* This symbol is defined in shared libraries. Define it here
 * (to nothing) in case this isn't a shared library. 
 */
#ifndef LIB_libformatrep_C_API 
#define LIB_libformatrep_C_API /* No special import/export declaration */
#endif

/* GENERAL LIBRARY FUNCTIONS -- START */

extern LIB_libformatrep_C_API 
bool MW_CALL_CONV libformatrepInitializeWithHandlers(
       mclOutputHandlerFcn error_handler, 
       mclOutputHandlerFcn print_handler);

extern LIB_libformatrep_C_API 
bool MW_CALL_CONV libformatrepInitialize(void);

extern LIB_libformatrep_C_API 
void MW_CALL_CONV libformatrepTerminate(void);

extern LIB_libformatrep_C_API 
void MW_CALL_CONV libformatrepPrintStackTrace(void);

/* GENERAL LIBRARY FUNCTIONS -- END */

/* C INTERFACE -- MLX WRAPPERS FOR USER-DEFINED MATLAB FUNCTIONS -- START */

extern LIB_libformatrep_C_API 
bool MW_CALL_CONV mlxFormatrep(int nlhs, mxArray *plhs[], int nrhs, mxArray *prhs[]);

/* C INTERFACE -- MLX WRAPPERS FOR USER-DEFINED MATLAB FUNCTIONS -- END */

/* C INTERFACE -- MLF WRAPPERS FOR USER-DEFINED MATLAB FUNCTIONS -- START */

extern LIB_libformatrep_C_API bool MW_CALL_CONV mlfFormatrep(int nargout, mxArray** x, mxArray* n);

#ifdef __cplusplus
}
#endif
/* C INTERFACE -- MLF WRAPPERS FOR USER-DEFINED MATLAB FUNCTIONS -- END */

#endif
