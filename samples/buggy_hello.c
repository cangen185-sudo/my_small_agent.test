#include <stdio.h>
#include <stdlib.h>

int main() {
    char name[8];
    int *scores = malloc(sizeof(int) * 3);
    gets(name);
    for (int i = 0; i <= 3; i++) {
        scores[i] = i * 10;
    }
    printf("hello %s\n", name);
}

