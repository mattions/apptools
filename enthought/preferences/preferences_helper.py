""" An object that can be initialized from a preferences node. """


# Enthought library imports.
from enthought.traits.api import HasTraits, Str, Unicode


class PreferencesHelper(HasTraits):
    """ An object that can be initialized from a preferences node. """

    #### 'PreferencesHelper' *CLASS* interface ################################

    # The preferences node used by *ALL* preferences helpers.
    preferences = None # Instance(IPreferences)
    
    #### 'PreferencesHelper' interface ########################################

    # The path to the preference node that contains the preferences that we
    # use to initialize instances of this class.
    preferences_path = Str

    #### Private interface ####################################################

    # A flag that prevents us from setting a preference value twice.
    _event_handled = False
    
    ###########################################################################
    # 'object' interface.
    ###########################################################################

    def __init__(self, **traits):
        """ Constructor. """

        super(PreferencesHelper, self).__init__(**traits)

        # Initialize the object's traits from the preferences node.
        self._initialize(self.preferences)

        return

    ###########################################################################
    # Private interface.
    ###########################################################################

    #### Trait change handlers ################################################

    def _anytrait_changed(self, trait_name, old, new):
        """ Static trait change handler. """

        if not self._event_handled:
            if self._is_preference_trait(trait_name):
                path = self._get_path()
                self.preferences.set('%s.%s' % (path, trait_name), new)

        return

    #### Other observer pattern listeners #####################################
    
    def _preferences_changed_listener(self, node, key, old, new):
        """ Listener called when a preference value is changed. """

        if key in self.trait_names():
            self._event_handled = True
            setattr(self, key, self._get_value(key, new))
            self._event_handled = False

        return

    #### Methods ##############################################################

    def _get_path(self):
        """ Return the path to our preferences node. """

        if len(self.preferences_path) > 0:
            path = self.preferences_path

        else:
            path = getattr(self, 'PREFERENCES_PATH', None)
            if path is None:
                raise SystemError('no preferences path' % self)
            
        return path
            
    def _get_value(self, trait_name, value):
        """ Get the actual value to set.

        This method makes sure that any required work is done to convert the
        preference value from a string.

        """

        handler = self.trait(trait_name).handler

        # If the trait type is 'Str' then we just take the raw value.
        if type(handler) is Str:
            pass
            
        # If the trait type is 'Unicode' then we convert the raw value.
        elif type(handler) is Unicode:
            value = unicode(value)

        # Otherwise, we eval it!
        else:
            try:
                value = eval(value)

            # If the eval fails then there is probably a syntax error, but
            # we will let the handler validation throw the exception.
            except:
                pass

        return handler.validate(self, trait_name, value)

    def _initialize(self, preferences):
        """ Initialize the object's traits from the preferences node. """

        path = self._get_path()
        keys = preferences.keys(path)

        traits_to_set = {}
        for trait_name in self.trait_names():
            if trait_name in keys:
                key = '%s.%s' % (path, trait_name)
                value = self._get_value(trait_name, preferences.get(key))
                traits_to_set[trait_name] = value
                
        self.set(trait_change_notify=False, **traits_to_set)

        # Listen for changes to the node's preferences.
        preferences.add_preferences_listener(
            self._preferences_changed_listener, path
        )

        return

    def _is_preference_trait(self, trait_name):
        """ Return True if a trait represents a preference value. """

        if trait_name.startswith('_') or trait_name.endswith('_') \
           or trait_name in ['preferences', 'preferences_path']:
            return False

        return True

#### EOF ######################################################################