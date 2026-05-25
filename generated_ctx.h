#pragma once
#include "Utils/Ver1/Utils.h"

/* Auto Made By Tom from scanner.py from main.c -- DO NOT EDIT HIS WORK */

extern int hp;
extern float speed;
extern const char* name;
extern const char* person;

extern Var   _VARS[];
extern int   _VAR_COUNT;

/* Usage: BUILD_CTX(my_ctx); then pass &my_ctx to core_print */
#define BUILD_CTX(name) \
  Context name = {_VARS, _VAR_COUNT}
