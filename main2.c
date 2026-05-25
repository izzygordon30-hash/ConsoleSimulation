#include <stdio.h>
#include <stdarg.h>
#include <string.h>

void core_print(const char* string, ...) {

    printf("[CORE]: ");


    va_list args;
    va_start(args, string);

    #define INT_MAX 5
    #define STR_MAX 8
    #define FLT_MAX 8

    while (*string) {

        if (strncmp(string, "{int}", INT_MAX) == 0) {
            int value = va_arg(args, int);
            printf("%d", value);

            string += INT_MAX;
            continue;
        }

        
        if (strncmp(string, "{string}", STR_MAX) == 0) {
            const char* value = va_arg(args, const char*);
            printf("%s", value);

            string += STR_MAX; //no magic numbers grrrrr lol
            continue;
        }

        if (strncmp(string, "{float}", FLT_MAX) == 0) {
            double value = va_arg(args, double);
            printf("%f", value);

            string += FLT_MAX; //no magic numbers grrrrr lol
            continue;
        }

        putchar(*string);
        string++;
    }

    va_end(args);
}

int main() {
    
    int a = 5;
    int *p = &a;
    *p = 7;
    
    const char* greeting = "Hello";    
    double degree = 78.9;

    core_print("Hello {float}", degree);

}