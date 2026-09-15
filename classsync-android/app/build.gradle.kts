plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.google.dagger.hilt.android")
    id("com.google.devtools.ksp")
}

// Activate Firebase's Gradle plugin only once the project-specific
// google-services.json has been added to app/.
if (file("google-services.json").exists()) {
    apply(plugin = "com.google.gms.google-services")
}

android {
    namespace = "com.classsync.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.classsync.app"
        minSdk = 26  // Android 8.0+
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // TODO: Update BASE_URL to Railway URL after first deploy (e.g. https://<name>.up.railway.app/)
        buildConfigField("String", "BASE_URL", "\"https://class-sync-ah7n.onrender.com/\"")
    }

    val releaseStoreFile = providers.gradleProperty("CLASSSYNC_RELEASE_STORE_FILE").orNull
    val releaseStorePassword = providers.gradleProperty("CLASSSYNC_RELEASE_STORE_PASSWORD").orNull
    val releaseKeyAlias = providers.gradleProperty("CLASSSYNC_RELEASE_KEY_ALIAS").orNull
    val releaseKeyPassword = providers.gradleProperty("CLASSSYNC_RELEASE_KEY_PASSWORD").orNull
    val hasReleaseSigning = listOf(
        releaseStoreFile,
        releaseStorePassword,
        releaseKeyAlias,
        releaseKeyPassword,
    ).all { !it.isNullOrBlank() }

    signingConfigs {
        create("release") {
            if (hasReleaseSigning) {
                storeFile = file(releaseStoreFile!!)
                storePassword = releaseStorePassword
                keyAlias = releaseKeyAlias
                keyPassword = releaseKeyPassword
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            // TODO: Update BASE_URL to Railway URL after first deploy
            buildConfigField("String", "BASE_URL", "\"https://class-sync-ah7n.onrender.com/\"")
            if (hasReleaseSigning) signingConfig = signingConfigs.getByName("release")
        }
        debug {
            isMinifyEnabled = false
            // 10.0.2.2 maps to host loopback on Android emulator
            // TODO: Update BASE_URL to Railway URL after first deploy
            buildConfigField("String", "BASE_URL", "\"https://class-sync-ah7n.onrender.com/\"")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs += listOf("-opt-in=androidx.compose.material3.ExperimentalMaterial3Api")
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    lint {
        abortOnError = true
        checkReleaseBuilds = true
    }

    testOptions {
        unitTests.isReturnDefaultValues = true
    }
}

dependencies {
    // ── Compose BOM ──────────────────────────────────────────────────────
    val composeBom = platform("androidx.compose:compose-bom:2024.12.01")
    implementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    debugImplementation("androidx.compose.ui:ui-tooling")

    // ── Core & Lifecycle ─────────────────────────────────────────────────
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.activity:activity-compose:1.9.3")

    // ── Navigation ───────────────────────────────────────────────────────
    implementation("androidx.navigation:navigation-compose:2.8.5")
    implementation("androidx.hilt:hilt-navigation-compose:1.2.0")

    // ── Hilt (Dependency Injection) ──────────────────────────────────────
    implementation("com.google.dagger:hilt-android:2.51.1")
    ksp("com.google.dagger:hilt-compiler:2.51.1")

    // ── Networking (Retrofit + OkHttp) ───────────────────────────────────
    implementation("com.squareup.retrofit2:retrofit:2.11.0")
    implementation("com.squareup.retrofit2:converter-gson:2.11.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // ── DataStore & Security ─────────────────────────────────────────────
    implementation("androidx.datastore:datastore-preferences:1.1.1")
    implementation("androidx.security:security-crypto:1.1.0-alpha06")

    // ── Image Loading ────────────────────────────────────────────────────
    implementation("io.coil-kt:coil-compose:2.7.0")

    // ── Firebase (Push Notifications) ────────────────────────────────────
    implementation(platform("com.google.firebase:firebase-bom:33.7.0"))
    implementation("com.google.firebase:firebase-messaging-ktx")

    // ── WebView ──────────────────────────────────────────────────────────
    implementation("androidx.webkit:webkit:1.12.1")

    // ── Animations ───────────────────────────────────────────────────────
    implementation("com.airbnb.android:lottie-compose:6.6.2")

    // ── Splash Screen ────────────────────────────────────────────────────
    implementation("androidx.core:core-splashscreen:1.0.1")

    // ── SwipeRefresh ─────────────────────────────────────────────────────
    implementation("com.google.accompanist:accompanist-swiperefresh:0.36.0")

    // ── Testing ──────────────────────────────────────────────────────────
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
    androidTestImplementation(composeBom)
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
}
