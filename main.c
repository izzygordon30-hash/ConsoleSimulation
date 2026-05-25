/**
 * main.c the actual game/engine code
 *  - Run: python scanner.py main.c
 *  - Then compile all three .c files together
 */

#include <stdio.h>
#include "Utils/Ver1/Utils.h"
#include "generated_ctx.h"

/**
 * These are the Varibles scanner.py detected 
 */

int hp = 100;
float speed = 3.5f;
const char* name = "Isaiah";
const char* person  = "Mr Bake";



int main(void) {

    /* Build a Context form the generated registry - one line, stack only */
    BUILD_CTX(ctx);

    const char* error = "Mr Bake";
    int dmg = 12;

    /** --- Context path: scanner.py handled the wiring --- */
    core_print(LOG_INFO, "THIS INT {to}",  &ctx);
    core_print(LOG_INFO, "Player: {person}", &ctx);
    core_print(LOG_INFO, "HP: {hp}",       &ctx);
    core_print(LOG_WARN, "Speed: {speed}", &ctx);
    core_print(LOG_INFO, "Speed: {T}", &ctx);
    

    float degrees = 45.0f;

    /** --- Variadic path: no ctx needed --- */
    core_print(LOG_INFO, "Frame: {int}",   NULL, 42);
    core_print(LOG_WARN, "Ratio: {float}", NULL, 0.75f);
    core_print(LOG_ERR,  "Sector {string} offline",  NULL, "B-7");

    /** --- Plain String --- */
    core_print(LOG_ERR, "Null pointer in the render pass", NULL);

    return 0;
}