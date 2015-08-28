__author__ = 'Peter Sottile'

def unpack(breath, unpack_col = unpack_col):
        """

        :type breath: object
        """
        for col in unpack_col:
            key_names = set()
            keys = set()
            key = ''

            try:
                keys = breath[col].apply(lambda x: set(x.keys()) if isinstance(x, dict) else set())
            except:
                print(sys.exc_info()[0])

            try:
                for items in keys:
                    key_names.update(items)
            except:
                print(sys.exc_info()[0])
                print(keys)

            try:
                for key in key_names:
                    breath[col +':'+ key] = breath[col].apply(lambda x: x[key] if (isinstance(x, dict) and (key in x)) else np.nan)
                breath.drop(col, inplace=True, axis=1)
            except:
                print(sys.exc_info()[0])
                print('last', key, key_names)

        return breath

def plotted(analysis_df, n_max, n_min, **kwargs):
        analysis_df.plot(y=['flow','paw', 'smooth', 'volume'], sharex=True, secondary_y=['volume'])

        for x in np.nditer(n_max):
            try:
                plt.axvline(x=analysis_df['time'].iloc[int(x)])
            except:
                print('plt', sys.exc_info()[0])

        for x in np.nditer(n_min):
            try:
                plt.axvline(x=analysis_df['time'].iloc[int(x)], color='r')
            except:
                print('plt', sys.exc_info()[0])

        len_at_end = analysis_df[analysis_df.status == 1].shape[0]
        status_df = analysis_df[:len_at_end - 3]
        tempx = status_df['time'].values[-1]
        #plt.axvline(x=tempx, color ='g')
