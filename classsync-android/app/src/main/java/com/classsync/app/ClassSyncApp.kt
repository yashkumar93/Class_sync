package com.classsync.app

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/**
 * ClassSync Application class — initialises Hilt dependency injection.
 */
@HiltAndroidApp
class ClassSyncApp : Application()
