package com.classsync.app.di

import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

/**
 * Repository classes use constructor injection today. This module is reserved
 * for interface bindings as feature repositories acquire test doubles.
 */
@Module
@InstallIn(SingletonComponent::class)
object RepositoryModule
