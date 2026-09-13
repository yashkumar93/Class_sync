# Proguard rules for ClassSync
-keepattributes Signature
-keepattributes *Annotation*

# Retrofit
-dontwarn retrofit2.**
-keep class retrofit2.** { *; }
-keepattributes Exceptions

# Gson
-keep class com.classsync.app.data.remote.dto.** { *; }

# Hilt
-keep class dagger.hilt.** { *; }
