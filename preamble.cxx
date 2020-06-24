extern "C" {
int _fltused = 0;
}

using int8_t = signed char;
using int16_t = signed short int;
using int32_t = signed int;
using int64_t = signed long long int;

using uint8_t = unsigned char;
using uint16_t = unsigned short int;
using uint32_t = unsigned int;
using uint64_t = unsigned long long int;

using f32_t = float;
using f64_t = double;

template<class T, T v>
struct integral_constant {
    static constexpr T value = v;
    using value_type = T;
    using type = integral_constant;
    constexpr operator value_type() const noexcept { return value; }
    constexpr value_type operator()() const noexcept { return value; }
};

template<bool B>
using bool_constant = integral_constant<bool, B>;

using false_type = bool_constant<false>;
using true_type = bool_constant<true>;

template<typename T, typename U>
struct is_same : false_type {};
 
template<typename T>
struct is_same<T, T> : true_type {};

template<typename T, typename U>
inline constexpr bool is_same_v = is_same<T, U>::value;

template<typename T>
__declspec(noinline) T use(T a) {
    if constexpr (is_same_v<T, f32_t>) {
        uint32_t v = *reinterpret_cast<uint32_t*>(&a);
        v = static_cast<uint64_t>(v) * 0x5851F42D4C957F2D + 0x14057B7EF767814F;
        return *reinterpret_cast<f32_t*>(&v);
    } else if constexpr (is_same_v<T, f64_t>) {
        uint64_t v = *reinterpret_cast<uint64_t*>(&a);
        v = v * 0x5851F42D4C957F2D + 0x14057B7EF767814F;
        return *reinterpret_cast<f64_t*>(&v);
    } else {
        return static_cast<T>(static_cast<uint64_t>(a) * 0x5851F42D4C957F2D + 0x14057B7EF767814F);
    }
}
