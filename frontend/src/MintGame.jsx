import { useState } from "react";
import { useEnokiFlow } from "@mysten/enoki/react";
import { useLogin } from "./UserContext"; // Assuming UserContext provides userDetails
import { getFullnodeUrl, SuiClient } from "@mysten/sui/client";
import { Transaction } from "@mysten/sui/transactions";
import { bcs } from '@mysten/sui/bcs';

// --- Configuration Constants ---
const NETWORK = "testnet"; // Or "mainnet", "devnet"
const FULLNODE_URL = getFullnodeUrl(NETWORK);
const AI_GAME_GENERATOR_PACKAGE_ID = "0xa321a43ec3eaccc412337b474f627a6e9bd5eee2df4fba4b1f7b281c1f9317ea";
const GAME_BOOK_OBJECT_ID = "0xa63e89b692e4dd37e3ed2a9cb574d6194e2fbb9409161a6a7afbc01c0fe540b2";
const DEFAULT_GAME_PROMPT = "My Awesome Game Idea"; // Example prompt
const CURRENT_DATE = "2025-04-24 09:39:29";
const CURRENT_USER = "Rishikesh0523";

// --- Component ---
const MintGame = () => {
    
    const flow = useEnokiFlow();
    const { userDetails } = useLogin(); // Get user details from context
    const [txnDigest, setTxnDigest] = useState(); // Store the transaction digest
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(); // Store potential errors

    const handleCreateGame = async () => {
        if (!userDetails) {
            setError("Please log in first.");
            return;
        }
        if (!flow) {
            setError("Enoki Flow not available.");
            return;
        }

        setLoading(true);
        setTxnDigest(null);
        setError(null);

        try {
            console.log(`Using network: ${NETWORK} (${FULLNODE_URL})`);
            const suiClient = new SuiClient({ url: FULLNODE_URL });
            const keypair = await flow.getKeypair({ network: NETWORK });

            console.log("User Address:", keypair.getPublicKey().toSuiAddress());
            console.log("GameBook Object ID:", GAME_BOOK_OBJECT_ID);
            console.log("Package ID:", AI_GAME_GENERATOR_PACKAGE_ID);

            const txb = new Transaction();

            // Define the game prompt
            const gamePrompt = DEFAULT_GAME_PROMPT;

            // Convert string to Uint8Array using TextEncoder
            const promptBytes = new TextEncoder().encode(gamePrompt);

            // Encode as vector<u8> using BCS
            const gamePromptBytes = bcs.vector(bcs.u8()).serialize(Array.from(promptBytes)).toBytes();

            // Serialize 0 as u64 using BCS (you can also pass a bigint like `0n`)
            const zeroU64 = bcs.U64.serialize(0).toBytes();
            txb.setSender(keypair.getPublicKey().toSuiAddress());

            // Now pass it to `txb.pure` WITHOUT a type string
            txb.moveCall({
                target: `${AI_GAME_GENERATOR_PACKAGE_ID}::ai_game_generator::create_game_shared`,
                arguments: [
                    txb.object(GAME_BOOK_OBJECT_ID),
                    txb.pure(gamePromptBytes),         // <- already serialized with bcs
                    txb.pure(zeroU64)                  // <- this too!
                ],
                typeArguments: [],
            });

            console.log("Transaction block prepared. Signing and executing...");

            const builtTx = await txb.build({ client: suiClient });

            const txnRes = await suiClient.signAndExecuteTransaction({
                signer: keypair,
                transaction: builtTx,  // ✅ This is a Uint8Array
                options: {
                    showEffects: true,
                },
            });

            console.log("Transaction Response:", txnRes);

            if (txnRes?.digest) {
                console.log("Game creation successful. Digest:", txnRes.digest);
                setTxnDigest(txnRes.digest);
            } else {
                throw new Error("Transaction failed or digest not found in response.");
            }

        } catch (err) {
            console.error("Error creating game:", err);
            const errorMessage = err instanceof Error ? err.message : String(err) ?? "An unknown error occurred.";
            setError(`Failed to create game: ${errorMessage}`);
        } finally {
            setLoading(false);
        }
    };

    // Basic inline styles for demonstration (can be moved to CSS/Styled Components)
    const styles = {
        container: {
            padding: '20px',
            border: '1px solid #ccc',
            borderRadius: '8px',
            maxWidth: '500px',
            margin: '20px auto',
            fontFamily: 'Arial, sans-serif',
            textAlign: 'center',
        },
        button: (disabled) => ({
            padding: '10px 20px',
            fontSize: '16px',
            cursor: disabled ? 'not-allowed' : 'pointer',
            backgroundColor: disabled ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            opacity: disabled ? 0.6 : 1,
            marginTop: '15px',
        }),
        error: {
            color: 'red',
            marginTop: '10px',
            wordBreak: 'break-word',
        },
        success: {
            color: 'green',
            marginTop: '10px',
            wordBreak: 'break-word',
        },
        info: {
            color: '#666',
            marginTop: '10px',
            fontSize: '14px',
        },
        link: {
            color: '#007bff',
            textDecoration: 'none',
        },
        footer: {
            marginTop: '20px',
            fontSize: '12px',
            color: '#888',
        }
    };

    return (
        <div className="mint-game-container" style={styles.container}>
            <h1>Mint New Game</h1>
            <p>This will create a new game entry on the Sui blockchain using your Enoki account.</p>

            {/* Display error message if any */}
            {error && <p style={styles.error}>Error: {error}</p>}

            {/* Display success message and digest */}
            {txnDigest && (
                <p style={styles.success}>
                    Game Created Successfully! <br />
                    Transaction Digest:{" "}
                    <a
                        href={`https://suiscan.xyz/${NETWORK}/tx/${txnDigest}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={styles.link}
                    >
                        {txnDigest}
                    </a>
                </p>
            )}

            {/* Action Button */}
            <button
                onClick={handleCreateGame}
                disabled={loading || !userDetails || !flow}
                style={styles.button(loading || !userDetails || !flow)}
                title={!userDetails ? "Please log in to create a game" : !flow ? "Enoki flow not ready" : ""}
            >
                {loading ? "Creating..." : "Create Game"}
            </button>

            {/* Inform user if they need to log in */}
            {!userDetails && <p style={styles.info}>Please log in to enable game creation.</p>}

            {/* Footer with user and date information */}
            <div style={styles.footer}>
                User: {CURRENT_USER} | Last updated: {CURRENT_DATE}
            </div>
        </div>
    );
}

export default MintGame;