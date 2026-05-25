#include "core.h"
#include "Utils.h"
#include <stdio.h>
#include <stdarg.h>
#include <string.h>

static int sparse[MAX_ENTITIES];
static Entity dense[MAX_ENTITIES];
static Health health_dense[MAX_ENTITIES];

static int size = 0;





/**
 * ## Init.
 * Sets up the Core.
 */
void init_core() {
    for (int i = 0; i < MAX_ENTITIES; i++) {
        sparse[i] = -1;
    }
    size = 0;
    core_print_info("Sparse ECS initialized\n");
}

Entity create_entity() {
    Entity e = size;

    dense[size] = e;
    health_dense[size].health = 100;

    sparse[e] = size;

    size++;

    core_print_info("Entity %s created\n", e);
    return e;

}