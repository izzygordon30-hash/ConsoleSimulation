#pragma once
#include <stdint.h> // For Unsigned Integers

#define MAX_ENTITIES 1024

typedef uint32_t Entity;

// Sparse set ECS storage
typedef struct Health {
    int health;
} Health;