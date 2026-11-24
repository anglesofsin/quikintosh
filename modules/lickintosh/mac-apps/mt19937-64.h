/* MT19937-64 parameters specified by C++ std::mt19937_64.
 * GameplayKit documents this exact engine for GKMersenneTwisterRandomSource:
 * https://developer.apple.com/documentation/gameplaykit/gkmersennetwisterrandomsource
 */
typedef unsigned long long QIMTWord;
typedef struct { QIMTWord words[312]; unsigned index; } QIMTState;

static void qi_mt_seed(QIMTState *state, QIMTWord seed) {
    state->words[0] = seed;
    for (unsigned i = 1; i < 312; ++i)
        state->words[i] = 6364136223846793005ULL *
            (state->words[i-1] ^ (state->words[i-1] >> 62)) + i;
    state->index = 312;
}

static QIMTWord qi_mt_next(QIMTState *state) {
    if (state->index == 312) {
        for (unsigned i = 0; i < 312; ++i) {
            QIMTWord combined = (state->words[i] & 0xFFFFFFFF80000000ULL) |
                               (state->words[(i+1) % 312] & 0x7FFFFFFFULL);
            state->words[i] = state->words[(i+156) % 312] ^ (combined >> 1) ^
                             ((combined & 1) ? 0xB5026F5AA96619E9ULL : 0);
        }
        state->index = 0;
    }
    QIMTWord value = state->words[state->index++];
    value ^= (value >> 29) & 0x5555555555555555ULL;
    value ^= (value << 17) & 0x71D67FFFEDA60000ULL;
    value ^= (value << 37) & 0xFFF7EEE000000000ULL;
    return value ^ (value >> 43);
}
