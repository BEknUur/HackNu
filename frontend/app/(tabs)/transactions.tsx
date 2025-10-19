import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    Modal,
    TextInput,
    Alert,
    RefreshControl,
    ActivityIndicator,
    Platform,
  } from 'react-native';
  import { useState, useEffect, useCallback } from 'react';
  import { Ionicons } from '@expo/vector-icons';
  import { ZamanColors } from '@/constants/theme';
  import {
    getUserAccounts,
    getUserTransactions,
    createDeposit,
    createWithdrawal,
    createTransfer,
    createAccount,
    Account,
    Transaction,
  } from '@/lib/api-client';
  
  interface UserData {
    id: number;
    name: string;
    surname: string;
    email: string;
  }
  
  type TransactionModalType = 'deposit' | 'withdrawal' | 'transfer' | null;
  
  export default function TransactionsScreen() {
    const [user, setUser] = useState<UserData | null>(null);
    const [account, setAccount] = useState<Account | null>(null);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [modalType, setModalType] = useState<TransactionModalType>(null);
    const [processing, setProcessing] = useState(false);
  
    // Form state
    const [amount, setAmount] = useState('');
    const [toAccountId, setToAccountId] = useState('');
    const [description, setDescription] = useState('');
  
    useEffect(() => {
      loadUser();
    }, []);
  
    useEffect(() => {
      if (user) {
        loadData();
      }
    }, [user]);
  
    function loadUser() {
      try {
        if (typeof localStorage !== 'undefined') {
          const userJson = localStorage.getItem('user');
          if (userJson) {
            setUser(JSON.parse(userJson));
          }
        }
      } catch (error) {
        console.error('Error loading user:', error);
      }
    }
  
    async function loadData() {
      if (!user) return;
  
      try {
        setLoading(true);
        
        // Try to get accounts
        let accountsData = await getUserAccounts(user.id);
        
        // If no account exists, create one automatically
        if (accountsData.length === 0) {
          console.log('No account found, creating default checking account...');
          const newAccount = await createAccount({
            user_id: user.id,
            account_type: 'checking',
            balance: 0,
            currency: 'KZT',
          });
          accountsData = [newAccount];
        }
  
        // Get transactions
        const transactionsData = await getUserTransactions(user.id, { limit: 100 });
  
        if (accountsData.length > 0) {
          setAccount(accountsData[0]);
        }
        setTransactions(transactionsData);
      } catch (error) {
        console.error('Error loading data:', error);
        if (Platform.OS === 'web') {
          alert(`Error: ${error instanceof Error ? error.message : 'Failed to load data'}`);
        } else {
          Alert.alert('Error', error instanceof Error ? error.message : 'Failed to load data');
        }
      } finally {
        setLoading(false);
      }
    }
  
    const onRefresh = useCallback(async () => {
      setRefreshing(true);
      await loadData();
      setRefreshing(false);
    }, [user]);
  
    function openModal(type: TransactionModalType) {
      setModalType(type);
      setAmount('');
      setToAccountId('');
      setDescription('');
    }
  
    function closeModal() {
      setModalType(null);
      setAmount('');
      setToAccountId('');
      setDescription('');
    }
  
    async function handleTransaction() {
      if (!user || !account) return;
  
      const amountNum = parseFloat(amount);
      if (isNaN(amountNum) || amountNum <= 0) {
        if (Platform.OS === 'web') {
          alert('Please enter a valid amount');
        } else {
          Alert.alert('Invalid Amount', 'Please enter a valid amount');
        }
        return;
      }
  
      try {
        setProcessing(true);
  
        if (modalType === 'deposit') {
          await createDeposit(user.id, {
            account_id: account.id,
            amount: amountNum,
            currency: account.currency,
            description: description || undefined,
          });
        } else if (modalType === 'withdrawal') {
          await createWithdrawal(user.id, {
            account_id: account.id,
            amount: amountNum,
            currency: account.currency,
            description: description || undefined,
          });
        } else if (modalType === 'transfer') {
          const toAccountIdNum = parseInt(toAccountId);
          if (isNaN(toAccountIdNum) || toAccountIdNum <= 0) {
            if (Platform.OS === 'web') {
              alert('Please enter a valid account ID');
            } else {
              Alert.alert('Invalid Account ID', 'Please enter a valid account ID');
            }
            return;
          }
  
          await createTransfer(user.id, {
            from_account_id: account.id,
            to_account_id: toAccountIdNum,
            amount: amountNum,
            currency: account.currency,
            description: description || undefined,
          });
        }
  
        closeModal();
        await loadData();
  
        if (Platform.OS === 'web') {
          alert('Transaction completed successfully!');
        } else {
          Alert.alert('Success', 'Transaction completed successfully!');
        }
      } catch (error) {
        console.error('Error creating transaction:', error);
        if (Platform.OS === 'web') {
          alert(`Error: ${error instanceof Error ? error.message : 'Transaction failed'}`);
        } else {
          Alert.alert('Error', error instanceof Error ? error.message : 'Transaction failed');
        }
      } finally {
        setProcessing(false);
      }
    }
  
    function formatDate(dateString: string): string {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    }
  
    function getTransactionColor(type: string): string {
      switch (type) {
        case 'deposit':
          return ZamanColors.persianGreen;
        case 'withdrawal':
          return ZamanColors.persianGreen;
        case 'transfer':
          return ZamanColors.persianGreen;
        case 'purchase':
          return ZamanColors.persianGreen;
        default:
          return ZamanColors.gray[500];
      }
    }
  
    function getTransactionIcon(type: string): any {
      switch (type) {
        case 'deposit':
          return 'arrow-down-circle';
        case 'withdrawal':
          return 'arrow-up-circle';
        case 'transfer':
          return 'swap-horizontal';
        case 'purchase':
          return 'cart';
        default:
          return 'cash';
      }
    }
  
    if (loading) {
      return (
        <View style={[styles.container, styles.centerContent]}>
          <ActivityIndicator size="large" color={ZamanColors.persianGreen} />
          <Text style={styles.loadingText}>Loading wallet...</Text>
        </View>
      );
    }
  
    if (!account) {
      return (
        <View style={[styles.container, styles.centerContent]}>
          <Ionicons name="wallet-outline" size={80} color={ZamanColors.gray[400]} />
          <Text style={styles.emptyStateText}>No account found</Text>
          <Text style={styles.emptyStateSubtext}>Please contact support</Text>
        </View>
      );
    }
  
    return (
      <View style={styles.container}>
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.contentContainer}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.headerTitle}>Wallet</Text>
          </View>
  
          {/* Balance Card */}
          <View style={styles.balanceCard}>
            <Text style={styles.balanceLabel}>Current Balance</Text>
            <Text style={styles.balanceAmount}>
              {parseFloat(account.balance).toFixed(2)} {account.currency}
            </Text>
            <View style={styles.accountInfo}>
              <View style={styles.accountInfoItem}>
                <Text style={styles.accountInfoLabel}>Account Type</Text>
                <Text style={styles.accountInfoValue}>{account.account_type}</Text>
              </View>
              <View style={styles.accountInfoItem}>
                <Text style={styles.accountInfoLabel}>Status</Text>
                <Text style={styles.accountInfoValue}>
                  {account.status}
                </Text>
              </View>
            </View>
          </View>
  
          {/* Action Buttons */}
          <View style={styles.actionsContainer}>
            <TouchableOpacity style={styles.actionButton} onPress={() => openModal('deposit')}>
              <View style={styles.actionIconContainer}>
                <Ionicons name="arrow-down-circle" size={20} color={ZamanColors.persianGreen} />
              </View>
              <Text style={styles.actionButtonText}>Deposit</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionButton} onPress={() => openModal('withdrawal')}>
              <View style={styles.actionIconContainer}>
                <Ionicons name="arrow-up-circle" size={20} color={ZamanColors.persianGreen} />
              </View>
              <Text style={styles.actionButtonText}>Withdraw</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionButton} onPress={() => openModal('transfer')}>
              <View style={styles.actionIconContainer}>
                <Ionicons name="swap-horizontal" size={20} color={ZamanColors.persianGreen} />
              </View>
              <Text style={styles.actionButtonText}>Transfer</Text>
            </TouchableOpacity>
          </View>
  
          {/* Transaction History */}
          <View style={styles.historySection}>
            <Text style={styles.sectionTitle}>Transaction History</Text>
  
            {transactions.length === 0 ? (
              <View style={styles.emptyTransactions}>
                <Ionicons name="receipt-outline" size={60} color={ZamanColors.gray[400]} />
                <Text style={styles.emptyTransactionsText}>No transactions yet</Text>
              </View>
            ) : (
              transactions.map((transaction) => (
                <View key={transaction.id} style={styles.transactionItem}>
                  <View style={styles.transactionIcon}>
                    <Ionicons
                      name={getTransactionIcon(transaction.transaction_type)}
                      size={20}
                      color={getTransactionColor(transaction.transaction_type)}
                    />
                  </View>
  
                  <View style={styles.transactionDetails}>
                    <Text style={styles.transactionType}>{transaction.transaction_type}</Text>
                    <Text style={styles.transactionDate}>{formatDate(transaction.created_at)}</Text>
                    {transaction.description && (
                      <Text style={styles.transactionDescription}>{transaction.description}</Text>
                    )}
                  </View>
  
                  <Text style={styles.transactionAmount}>
                    {transaction.transaction_type === 'deposit'
                      ? '+'
                      : transaction.transaction_type === 'withdrawal' || transaction.transaction_type === 'purchase'
                      ? '-'
                      : transaction.transaction_type === 'transfer' && transaction.user_id === user?.id
                      ? '-'
                      : '+'}
                    {parseFloat(transaction.amount).toFixed(2)} {transaction.currency}
                  </Text>
                </View>
              ))
            )}
          </View>
        </ScrollView>
  
        {/* Transaction Modal */}
        <Modal visible={modalType !== null} animationType="slide" transparent presentationStyle="overFullScreen">
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalHeader}>
                <Text style={styles.modalTitle}>
                  {modalType === 'deposit' ? 'Deposit' : modalType === 'withdrawal' ? 'Withdrawal' : 'Transfer'}
                </Text>
                <TouchableOpacity onPress={closeModal}>
                  <Ionicons name="close" size={28} color={ZamanColors.gray[600]} />
                </TouchableOpacity>
              </View>
  
              <View style={styles.modalBody}>
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Amount</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="0.00"
                    keyboardType="decimal-pad"
                    value={amount}
                    onChangeText={setAmount}
                  />
                </View>
  
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Currency</Text>
                  <TextInput style={[styles.input, styles.inputReadonly]} value={account.currency} editable={false} />
                </View>
  
                {modalType === 'transfer' && (
                  <View style={styles.inputGroup}>
                    <Text style={styles.inputLabel}>To Account ID</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="Enter account ID"
                      keyboardType="number-pad"
                      value={toAccountId}
                      onChangeText={setToAccountId}
                    />
                  </View>
                )}
  
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Description (Optional)</Text>
                  <TextInput
                    style={[styles.input, styles.inputMultiline]}
                    placeholder="Add a note..."
                    multiline
                    numberOfLines={3}
                    value={description}
                    onChangeText={setDescription}
                  />
                </View>
  
                {modalType === 'withdrawal' && (
                  <View style={styles.warningBox}>
                    <Ionicons name="information-circle" size={20} color="#FF9800" />
                    <Text style={styles.warningText}>
                      Available: {parseFloat(account.balance).toFixed(2)} {account.currency}
                    </Text>
                  </View>
                )}
              </View>
  
              <View style={styles.modalFooter}>
                <TouchableOpacity style={styles.cancelButton} onPress={closeModal} disabled={processing}>
                  <Text style={styles.cancelButtonText}>Cancel</Text>
                </TouchableOpacity>
  
                <TouchableOpacity
                  style={[styles.confirmButton, processing && styles.confirmButtonDisabled]}
                  onPress={handleTransaction}
                  disabled={processing}
                >
                  {processing ? (
                    <ActivityIndicator size="small" color="white" />
                  ) : (
                    <Text style={styles.confirmButtonText}>Confirm</Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      </View>
    );
  }
  
  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: ZamanColors.white,
    },
    centerContent: {
      justifyContent: 'center',
      alignItems: 'center',
    },
    scrollView: {
      flex: 1,
    },
    contentContainer: {
      paddingBottom: 100,
    },
    loadingText: {
      marginTop: 16,
      fontSize: 16,
      color: ZamanColors.gray[600],
    },
    emptyStateText: {
      marginTop: 16,
      fontSize: 18,
      fontWeight: '600',
      color: ZamanColors.gray[700],
    },
    emptyStateSubtext: {
      marginTop: 8,
      fontSize: 14,
      color: ZamanColors.gray[500],
    },
    header: {
      paddingTop: Platform.OS === 'ios' ? 60 : 40,
      paddingHorizontal: 24,
      paddingBottom: 16,
      backgroundColor: ZamanColors.white,
    },
    headerTitle: {
      fontSize: 24,
      fontWeight: '600',
      color: ZamanColors.black,
      letterSpacing: 0.3,
    },
    balanceCard: {
      backgroundColor: ZamanColors.white,
      marginHorizontal: 24,
      borderRadius: 16,
      padding: 20,
      borderWidth: 2,
      borderColor: ZamanColors.persianGreen,
      shadowColor: ZamanColors.persianGreen,
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.1,
      shadowRadius: 8,
      elevation: 5,
    },
    balanceLabel: {
      fontSize: 11,
      color: ZamanColors.gray[600],
      fontWeight: '500',
      textTransform: 'uppercase',
      letterSpacing: 0.8,
      marginBottom: 8,
    },
    balanceAmount: {
      fontSize: 32,
      fontWeight: '700',
      color: ZamanColors.persianGreen,
      marginBottom: 16,
    },
    accountInfo: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingTop: 16,
      borderTopWidth: 1,
      borderTopColor: ZamanColors.gray[200],
    },
    accountInfoItem: {
      flex: 1,
    },
    accountInfoLabel: {
      fontSize: 10,
      color: ZamanColors.gray[500],
      fontWeight: '500',
      textTransform: 'uppercase',
      letterSpacing: 0.4,
      marginBottom: 4,
    },
    accountInfoValue: {
      fontSize: 13,
      fontWeight: '600',
      color: ZamanColors.black,
      textTransform: 'capitalize',
    },
    actionsContainer: {
      flexDirection: 'row',
      paddingHorizontal: 24,
      marginTop: 20,
      gap: 12,
    },
    actionButton: {
      flex: 1,
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      paddingVertical: 16,
      borderRadius: 12,
      backgroundColor: ZamanColors.white,
      borderWidth: 1,
      borderColor: ZamanColors.gray[300],
      gap: 8,
    },
    actionIconContainer: {
      width: 40,
      height: 40,
      borderRadius: 20,
      backgroundColor: ZamanColors.cloud,
      alignItems: 'center',
      justifyContent: 'center',
    },
    actionButtonText: {
      color: ZamanColors.black,
      fontSize: 12,
      fontWeight: '600',
    },
    historySection: {
      paddingHorizontal: 24,
      marginTop: 28,
    },
    sectionTitle: {
      fontSize: 15,
      fontWeight: '600',
      color: ZamanColors.black,
      marginBottom: 16,
      textTransform: 'uppercase',
      letterSpacing: 0.5,
    },
    emptyTransactions: {
      alignItems: 'center',
      justifyContent: 'center',
      paddingVertical: 40,
    },
    emptyTransactionsText: {
      marginTop: 16,
      fontSize: 16,
      color: ZamanColors.gray[500],
    },
    transactionItem: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: ZamanColors.white,
      borderWidth: 1,
      borderColor: ZamanColors.gray[300],
      borderRadius: 12,
      padding: 14,
      marginBottom: 10,
    },
    transactionIcon: {
      width: 44,
      height: 44,
      borderRadius: 22,
      alignItems: 'center',
      justifyContent: 'center',
      marginRight: 12,
      backgroundColor: ZamanColors.cloud,
    },
    transactionDetails: {
      flex: 1,
    },
    transactionType: {
      fontSize: 14,
      fontWeight: '600',
      color: ZamanColors.black,
      textTransform: 'capitalize',
      marginBottom: 2,
    },
    transactionDate: {
      fontSize: 11,
      color: ZamanColors.gray[500],
    },
    transactionDescription: {
      fontSize: 12,
      color: ZamanColors.gray[600],
      marginTop: 2,
    },
    transactionAmount: {
      fontSize: 15,
      fontWeight: '700',
      color: ZamanColors.persianGreen,
    },
    modalOverlay: {
      flex: 1,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      justifyContent: 'flex-end',
    },
    modalContent: {
      backgroundColor: ZamanColors.white,
      borderTopLeftRadius: 24,
      borderTopRightRadius: 24,
      paddingTop: 20,
      paddingBottom: Platform.OS === 'ios' ? 40 : 20,
      maxHeight: '80%',
    },
    modalHeader: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: 24,
      paddingBottom: 20,
      borderBottomWidth: 1,
      borderBottomColor: ZamanColors.gray[300],
    },
    modalTitle: {
      fontSize: 24,
      fontWeight: '600',
      color: ZamanColors.black,
    },
    modalBody: {
      paddingHorizontal: 24,
      paddingVertical: 20,
    },
    inputGroup: {
      marginBottom: 20,
    },
    inputLabel: {
      fontSize: 14,
      fontWeight: '600',
      color: ZamanColors.gray[700],
      marginBottom: 8,
    },
    input: {
      borderWidth: 1,
      borderColor: ZamanColors.gray[300],
      borderRadius: 12,
      paddingHorizontal: 16,
      paddingVertical: 12,
      fontSize: 16,
      color: ZamanColors.black,
      backgroundColor: ZamanColors.white,
    },
    inputReadonly: {
      backgroundColor: ZamanColors.gray[100],
      color: ZamanColors.gray[600],
    },
    inputMultiline: {
      minHeight: 80,
      textAlignVertical: 'top',
    },
    warningBox: {
      flexDirection: 'row',
      alignItems: 'center',
      backgroundColor: '#FFF3E0',
      padding: 12,
      borderRadius: 8,
      gap: 8,
    },
    warningText: {
      fontSize: 14,
      color: '#E65100',
      fontWeight: '500',
    },
    modalFooter: {
      flexDirection: 'row',
      paddingHorizontal: 24,
      gap: 12,
    },
    cancelButton: {
      flex: 1,
      paddingVertical: 16,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: ZamanColors.gray[300],
      alignItems: 'center',
    },
    cancelButtonText: {
      fontSize: 16,
      fontWeight: '600',
      color: ZamanColors.gray[700],
    },
    confirmButton: {
      flex: 1,
      paddingVertical: 16,
      borderRadius: 12,
      backgroundColor: ZamanColors.persianGreen,
      alignItems: 'center',
    },
    confirmButtonDisabled: {
      opacity: 0.6,
    },
    confirmButtonText: {
      fontSize: 16,
      fontWeight: '600',
      color: ZamanColors.white,
    },
  });
  
  