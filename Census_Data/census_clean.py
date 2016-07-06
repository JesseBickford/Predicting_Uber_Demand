import pandas as pd

# Read in our census data
demo = pd.read_csv('./2013_ACS_neighborhoods_raw/nbhddemographics.csv')
econ = pd.read_csv('./2013_ACS_neighborhoods_raw/nbhdeconomics.csv')
housing = pd.read_csv('./2013_ACS_neighborhoods_raw/nbhdhousing.csv')
social = pd.read_csv('./2013_ACS_neighborhoods_raw/nbhdsocial.csv')

# Drop the row created by the index in each DataFrame
for df in [demo,econ,housing,social]:
    df.drop('Unnamed: 0',axis=1,inplace=True)
# Drop the duplicate column names from 3 of the DataFrames
for df in [econ,housing,social]:
    df.drop(['GEOGNAME','GEOTYPE','nta'],axis=1,inplace=True)

# Merge our 4 DataFrames together
census = demo.merge(econ,on='GEOID',how='outer',suffixes=('','e'))
census = census.merge(housing,on='GEOID',how='outer',suffixes=('','h'))
census = census.merge(social,on='GEOID',how='outer',suffixes=('','s'))

# Define a dictionary to map from the census variable names to a descriptive
# string. Only the census variables we are keeping are in this dictionary.
census_key = {'MALEE':'num_males','FEME':'num_females','POPU5E':'age_5_under',
              'POP5T9E':'age_5_to_9','POP10T14E':'age_10_to_14',
              'POP15T19E':'age_15_to_19','POP20T24E':'age_20_to_24',
              'POP25T34E':'age_25_to_34','POP35T44E':'age_35_to_44',
              'POP45T54E':'age_45_to_54','POP55T59E':'age_55_to_59',
              'POP60T64E':'age_60_to_64','POP65T74E':'age_65_to_74',
              'POP75T84E':'age_75_to_84','POP85PLE':'age_85_over',
              'HSPE':'race_hispanic','WTNHE':'race_white','BLNHE':'race_black',
              'AIANNHE':'race_am_indian','ASNNHE':'race_asian',
              'CVEM16PLE':'employed','CVLFUEME':'unemployed',
              'NLFE':'not_labor_force','CW_DRVALNE':'commute_car_alone',
              'CW_CRPLDE':'commute_car_pool','CW_PBTRNSE':'commute_pub_transp',
              'CW_WLKDE':'commute_walk','CW_OTHE':'commute_other',
              'MTRVTME':'mean_travel_time_work','HHIU10E':'inc_10k_less',
              'HHI10T14E':'inc_10k_to_14k','HHI15T24E':'inc_15k_to_24k',
              'HHI25T34E':'inc_25k_to_34k','HHI35T49E':'inc_35k_to_49k',
              'HHI50T74E':'inc_50k_to_74k','HHI75T99E':'inc_75k_to_99k',
              'HI100T149E':'inc_100k_to_149k','HI150T199E':'inc_150k_to_199k',
              'HHI200PLE':'inc_200k_over','HUE':'total_housing_units',
              'NOVHCLAVE':'vehic_avail_none','VHCL1AVE':'vehic_avail_1',
              'VHCL2AVE':'vehic_avail_2','VHCL3PLAVE':'vehic_avail_3_plus',
              'MS_MNVMRDE':'m_married','MS_MMRDSPE':'m_married_separated',
              'MS_MSPE':'m_separated','MS_MWDE':'m_widowed',
              'MS_MDVCDE':'m_divorced','MS_FNVMRDE':'f_married',
              'MS_FMRDSPE':'f_married_separated','MS_FSPE':'f_separated',
              'MS_FWDE':'f_widowed','MS_FDVCDE':'f_divorced',
              'EA_LT9GE':'ed_less_9','EA_9T12NDE':'ed_9_to12',
              'EA_HSCGRDE':'ed_high_school','EA_SCLGNDE':'ed_some_college',
              'EA_BCHDE':'ed_bachelors','EA_GRDPFDE':'ed_graduate',
              'GEOGNAME':'nbhd_name', 'GEOID':'nbhd_id'}

# Get the column names from our combined census DataFrame
cols = census.columns.values

# Update the columns names that are in our census_key dictionary
for i in range(len(cols)):
    if cols[i] in census_key.keys():
        cols[i] = census_key[cols[i]]

# Set the DataFrame column names to our updated list of names
census.columns = cols

# Initialize a list to store the column names we are going to drop
to_drop = []
for name in census.columns.values:
    # The columns we are going to keep don't have any uppercase letters, so we
    # add any column name that has an uppercase to our list
    if any(c for c in name if c.isupper()):
        to_drop.append(name)
# Drop the unneeded columns
census.drop(to_drop,axis=1,inplace=True)

# Save our DataFrame to csv
census.to_csv('census_final.csv')
